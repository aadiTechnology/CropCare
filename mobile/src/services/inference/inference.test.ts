import "@/services/inference/latin1TextDecoder";
import { encode as encodePng } from "fast-png";
import { encode as encodeJpeg } from "jpeg-js";

import labelsJson from "../../../assets/models/tomato/labels.json";
import preprocessingJson from "../../../assets/models/tomato/preprocessing.json";
import { resizeRgbaToRgbFloat32 } from "@/services/inference/bilinearResize";
import {
  applyExifOrientation,
  decodeImageBytes,
  readJpegOrientation,
  type PixelImage,
} from "@/services/inference/decodeImageBytes";
import { DiagnosisFailure } from "@/services/inference/DiagnosisFailure";
import { interpretSoftmax } from "@/services/inference/interpretOutput";
import {
  parseLabelFile,
  parsePreprocessingFile,
  validateModelTensors,
} from "@/services/inference/modelContract";
import { createTomatoDiagnosisService } from "@/services/inference/tomatoDiagnosisService";

const labels = parseLabelFile(labelsJson);
const preprocessing = parsePreprocessingFile(preprocessingJson);

describe("tomato label and preprocessing contract", () => {
  it("maps each output index to the class code stored in labels.json", () => {
    expect(labels.labels).toHaveLength(10);
    expect(labels.labels.map((label) => label.code)).toEqual(
      labelsJson.labels.map((label) => label.code),
    );
    expect(labels.labels.every((label, index) => label.index === index && label.crop === "tomato")).toBe(
      true,
    );
    expect(labels.experiment).toBe("plantvillage_tomato");
  });

  it("keeps RGB float pixels in 0-255 because scaling is inside the model", () => {
    expect(preprocessing).toEqual({
      height: 224,
      width: 224,
      channels: 3,
      colorOrder: "RGB",
      dtype: "float32",
      valueMin: 0,
      valueMax: 255,
    });
    expect(preprocessingJson.internal_scaling.applied_inside_exported_model).toBe(true);
    expect(preprocessingJson.input.resize_method).toBe("bilinear");
  });

  it("rejects a model tensor that is not 224x224 RGB float32 or does not have 10 outputs", () => {
    expect(
      validateModelTensors(
        { dataType: "float32", shape: [1, 224, 224, 3] },
        { dataType: "float32", shape: [1, 10] },
        preprocessing,
        labels.labels.length,
      ),
    ).toEqual({ inputElements: 224 * 224 * 3, outputElements: 10 });

    expect(() =>
      validateModelTensors(
        { dataType: "uint8", shape: [1, 224, 224, 3] },
        { dataType: "float32", shape: [1, 10] },
        preprocessing,
        10,
      ),
    ).toThrow(DiagnosisFailure);
    expect(() =>
      validateModelTensors(
        { dataType: "float32", shape: [1, 192, 192, 3] },
        { dataType: "float32", shape: [1, 10] },
        preprocessing,
        10,
      ),
    ).toThrow(DiagnosisFailure);
    expect(() =>
      validateModelTensors(
        { dataType: "float32", shape: [1, 224, 224, 3] },
        { dataType: "float32", shape: [1, 9] },
        preprocessing,
        10,
      ),
    ).toThrow(DiagnosisFailure);
  });
});

describe("image pixels to model input", () => {
  it("resizes with bilinear sampling and does not divide by 255", () => {
    const white = rgbaImage(1, 1, [255, 255, 255, 255]);
    const stretched = resizeRgbaToRgbFloat32(white.rgba, 1, 1, 224, 224);
    expect(stretched).toHaveLength(224 * 224 * 3);
    expect(stretched[0]).toBe(255);
    expect(stretched[stretched.length - 1]).toBe(255);

    const pair = rgbaImage(2, 1, [0, 0, 0, 255, 255, 0, 0, 255]);
    const center = resizeRgbaToRgbFloat32(pair.rgba, 2, 1, 1, 1);
    expect(center[0]).toBeCloseTo(127.5);
    expect(center[1]).toBe(0);
    expect(center[2]).toBe(0);
  });

  it("decodes PNG and JPEG into RGBA pixels instead of passing encoded bytes through", () => {
    const png = encodePng({
      width: 2,
      height: 1,
      channels: 3,
      depth: 8,
      data: Uint8Array.from([10, 20, 30, 40, 50, 60]),
    });
    const decodedPng = decodeImageBytes(png);
    expect(decodedPng).toMatchObject({ width: 2, height: 1 });
    expect(Array.from(decodedPng?.rgba ?? []).slice(0, 4)).toEqual([10, 20, 30, 255]);

    const jpeg = encodeJpeg(
      {
        width: 8,
        height: 8,
        data: solidRgba(8, 8, [20, 40, 60, 255]),
      },
      100,
    );
    const decodedJpeg = decodeImageBytes(new Uint8Array(jpeg.data));
    expect(decodedJpeg?.width).toBe(8);
    expect(decodedJpeg?.height).toBe(8);
    expect(decodedJpeg?.rgba[0]).toBeGreaterThan(10);
    expect(decodedJpeg?.rgba[0]).toBeLessThan(40);
    expect(decodeImageBytes(Uint8Array.from([1, 2, 3, 4]))).toBeNull();
  });

  it("reads a JPEG orientation tag and rotates pixels before inference", () => {
    expect(readJpegOrientation(orientationMarker(6))).toBe(6);
    const rotated = applyExifOrientation(rgbaImage(2, 1, [255, 0, 0, 255, 0, 0, 255, 255]), 6);
    expect(rotated.width).toBe(1);
    expect(rotated.height).toBe(2);
    expect(Array.from(rotated.rgba.slice(0, 3))).toEqual([255, 0, 0]);
    expect(Array.from(rotated.rgba.slice(4, 7))).toEqual([0, 0, 255]);
  });
});

describe("tomato inference errors and output interpretation", () => {
  it("selects the class code for the highest finite softmax score", () => {
    const probabilities = [0, 0, 0, 0, 0.2, 0, 0, 0, 0, 0.8];
    const prediction = interpretSoftmax(probabilities, labels.labels);
    expect(prediction).toEqual({
      index: 9,
      code: labels.labels[9].code,
      score: 0.8,
    });
    expect(labels.labels[9].code).toBe("tomato_yellow_leaf_curl_virus");
  });

  it("refuses output that is the wrong length, non-finite, or not a softmax", () => {
    expect(() => interpretSoftmax([1, 0, 0], labels.labels)).toThrow(DiagnosisFailure);
    const nonFinite = Array.from({ length: 10 }, () => 0.1);
    nonFinite[3] = Number.NaN;
    expect(() => interpretSoftmax(nonFinite, labels.labels)).toThrow(DiagnosisFailure);
    expect(() => interpretSoftmax(Array.from({ length: 10 }, () => 0), labels.labels)).toThrow(
      DiagnosisFailure,
    );
  });

  it("returns the tomato class and model score without a remedy", async () => {
    const decode = jest.fn(async () => rgbaImage(1, 1, [10, 20, 30, 255]));
    const run = jest.fn(async (input: Float32Array) => {
      expect(input).toHaveLength(224 * 224 * 3);
      expect(input[0]).toBe(10);
      expect(input[1]).toBe(20);
      expect(input[2]).toBe(30);
      expect(input[input.length - 1]).toBe(30);
      const probabilities = new Float32Array(10);
      probabilities[2] = 1;
      return probabilities;
    });
    const service = createTomatoDiagnosisService({ labels, preprocessing, decode, run });

    const result = await service.analyze({
      cropType: "tomato",
      imageUri: "file:///leaf.jpg",
      mode: "offline",
    });

    expect(result.cropType).toBe("tomato");
    expect(result.predictedDiseaseClass).toBe(labels.labels[2].code);
    expect(result.confidence).toBe(1);
    expect(result.modelVersion).toBe("plantvillage_tomato");
    expect(result.remedyReference).toBeNull();
    expect(result.isDemo).toBe(false);
    expect(result.status).toBe("model_prediction");
    expect(result.id.startsWith("tomato-")).toBe(true);
  });

  it("does not run the tomato model for soybean or hide a failed image or model call", async () => {
    const decode = jest.fn(async () => rgbaImage(1, 1, [1, 2, 3, 255]));
    const run = jest.fn(async () => new Float32Array(10).fill(0.1));
    const service = createTomatoDiagnosisService({ labels, preprocessing, decode, run });

    await expect(
      service.analyze({ cropType: "soybean", imageUri: "file:///leaf.jpg", mode: "offline" }),
    ).rejects.toMatchObject({ code: "unsupported_crop" });
    expect(decode).not.toHaveBeenCalled();
    expect(run).not.toHaveBeenCalled();

    decode.mockRejectedValueOnce(new Error("unreadable"));
    await expect(
      service.analyze({ cropType: "tomato", imageUri: "file:///leaf.jpg", mode: "offline" }),
    ).rejects.toMatchObject({ code: "image_unreadable" });
    expect(run).not.toHaveBeenCalled();

    decode.mockResolvedValueOnce(rgbaImage(1, 1, [1, 2, 3, 255]));
    run.mockRejectedValueOnce(new Error("native failure"));
    await expect(
      service.analyze({ cropType: "tomato", imageUri: "file:///leaf.jpg", mode: "offline" }),
    ).rejects.toMatchObject({ code: "inference_failed" });

    decode.mockResolvedValueOnce(rgbaImage(1, 1, [1, 2, 3, 255]));
    run.mockRejectedValueOnce(new DiagnosisFailure("model_unavailable"));
    await expect(
      service.analyze({ cropType: "tomato", imageUri: "file:///leaf.jpg", mode: "offline" }),
    ).rejects.toMatchObject({ code: "model_unavailable" });
  });
});

function rgbaImage(width: number, height: number, rgba: number[]): PixelImage {
  return { width, height, rgba: Uint8Array.from(rgba) };
}

function solidRgba(width: number, height: number, pixel: number[]): Uint8Array {
  const rgba = new Uint8Array(width * height * 4);
  for (let index = 0; index < width * height; index += 1) {
    rgba.set(pixel, index * 4);
  }
  return rgba;
}

function orientationMarker(orientation: number): Uint8Array {
  const payload = [
    0x45, 0x78, 0x69, 0x66, 0x00, 0x00, 0x49, 0x49, 0x2a, 0x00, 0x08, 0x00, 0x00, 0x00, 0x01, 0x00, 0x12, 0x01,
    0x03, 0x00, 0x01, 0x00, 0x00, 0x00, orientation, 0x00, 0x00, 0x00,
  ];
  const length = payload.length + 2;
  return Uint8Array.from([0xff, 0xd8, 0xff, 0xe1, (length >> 8) & 0xff, length & 0xff, ...payload, 0xff, 0xd9]);
}
