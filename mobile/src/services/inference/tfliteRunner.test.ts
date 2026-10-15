import { Image } from "react-native";
import { loadTensorflowModel } from "react-native-fast-tflite";

import preprocessingJson from "../../../assets/models/tomato/preprocessing.json";
import { parsePreprocessingFile } from "@/services/inference/modelContract";
import { createTfliteRunner } from "@/services/inference/tfliteRunner";

jest.mock("react-native-fast-tflite", () => ({
  loadTensorflowModel: jest.fn(),
}));

jest.mock("../../../assets/models/tomato/model.tflite", () => ({
  __esModule: true,
  default: 42,
}));

jest.mock("expo-file-system", () => {
  class File {
    uri: string;
    exists = false;

    constructor(_directory: unknown, name: string) {
      this.uri = `file:///cache/${name}`;
    }

    create(): void {
      this.exists = true;
    }

    delete(): void {
      this.exists = false;
    }

    write(): void {}
  }

  return {
    File,
    Paths: { cache: "cache://" },
  };
});

const preprocessing = parsePreprocessingFile(preprocessingJson);
const loadModel = jest.mocked(loadTensorflowModel);

function modelInput(): Float32Array {
  const input = new Float32Array(224 * 224 * 3);
  input[0] = 12;
  return input;
}

function floatBuffer(values: number[]): ArrayBuffer {
  const floats = Float32Array.from(values);
  return floats.buffer.slice(floats.byteOffset, floats.byteOffset + floats.byteLength);
}

function fakeModel(output: ArrayBuffer | Uint8Array) {
  return {
    inputs: [{ name: "image_rgb_0_255", dataType: "float32", shape: [1, 224, 224, 3] }],
    outputs: [{ name: "class_probabilities", dataType: "float32", shape: [1, 10] }],
    run: jest.fn(async () => [output]),
  };
}

describe("on-device tomato model runner", () => {
  beforeEach(() => {
    loadModel.mockReset();
    Image.resolveAssetSource = jest.fn(() => ({
      uri: "http://10.0.0.1:8082/assets/model.tflite",
    })) as unknown as typeof Image.resolveAssetSource;
  });

  it("returns the 10 class probabilities from a float32 output buffer", async () => {
    const probabilities = [0, 0, 1, 0, 0, 0, 0, 0, 0, 0];
    loadModel.mockResolvedValue(fakeModel(floatBuffer(probabilities)) as never);

    const output = await createTfliteRunner(preprocessing, 10)(modelInput());

    expect(Array.from(output)).toEqual(probabilities);
    expect(loadModel).toHaveBeenCalledTimes(1);
    expect(loadModel.mock.calls[0]?.[1]).toEqual([]);
  });

  it("reads a 40-byte output as 10 floats instead of rejecting it", async () => {
    const floats = Float32Array.from([0, 0, 0, 0, 0, 0, 0, 0, 0, 1]);
    const bytes = new Uint8Array(floats.buffer.slice(0));
    loadModel.mockResolvedValue(fakeModel(bytes) as never);

    const output = await createTfliteRunner(preprocessing, 10)(modelInput());

    expect(output).toHaveLength(10);
    expect(output[9]).toBe(1);
  });

  it("rejects an output buffer that is not 10 float32 values", async () => {
    loadModel.mockResolvedValue(fakeModel(new ArrayBuffer(8)) as never);

    await expect(createTfliteRunner(preprocessing, 10)(modelInput())).rejects.toMatchObject({
      code: "inference_failed",
    });
  });

  it("loads a cached model file when the bundled asset cannot be opened", async () => {
    const probabilities = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0];
    loadModel.mockRejectedValueOnce(new Error("java.net.MalformedURLException"));
    loadModel.mockResolvedValueOnce(fakeModel(floatBuffer(probabilities)) as never);
    const downloaded = new Uint8Array(16);
    downloaded.set([0x54, 0x46, 0x4c, 0x33], 4);
    globalThis.fetch = jest.fn(async () => ({
      ok: true,
      status: 200,
      arrayBuffer: async () => downloaded.buffer,
    })) as unknown as typeof fetch;

    const output = await createTfliteRunner(preprocessing, 10)(modelInput());

    expect(Array.from(output)).toEqual(probabilities);
    expect(loadModel).toHaveBeenNthCalledWith(2, { url: "file:///cache/cropcare-tomato-model.tflite" }, []);
  });

  it("does not score a download that is not a TensorFlow Lite model", async () => {
    loadModel.mockRejectedValue(new Error("native asset load failed"));
    globalThis.fetch = jest.fn(async () => ({
      ok: true,
      status: 200,
      arrayBuffer: async () => Uint8Array.from([1, 2, 3, 4, 5, 6, 7, 8, 9]).buffer,
    })) as unknown as typeof fetch;

    await expect(createTfliteRunner(preprocessing, 10)(modelInput())).rejects.toMatchObject({
      code: "model_unavailable",
    });
    expect(loadModel).toHaveBeenCalledTimes(1);
  });
});
