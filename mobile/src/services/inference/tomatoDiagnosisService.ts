import type { DiagnosisRequest, DiagnosisResult } from "@/types";

import type { DiagnosisService } from "../diagnosis/DiagnosisService";
import { resizeRgbaToRgbFloat32 } from "./bilinearResize";
import { DiagnosisFailure, rethrowDiagnosisFailure } from "./DiagnosisFailure";
import type { PixelImage } from "./decodeImageBytes";
import { interpretSoftmax } from "./interpretOutput";
import type { LabelFile, PreprocessingSpec } from "./modelContract";

export type TomatoDiagnosisDependencies = {
  labels: LabelFile;
  preprocessing: PreprocessingSpec;
  decode: (uri: string) => Promise<PixelImage>;
  run: (input: Float32Array) => Promise<Float32Array>;
};

export function createTomatoDiagnosisService(dependencies: TomatoDiagnosisDependencies): DiagnosisService {
  return {
    async analyze(request: DiagnosisRequest): Promise<DiagnosisResult> {
      if (request.cropType !== "tomato") {
        throw new DiagnosisFailure("unsupported_crop");
      }

      const pixels = await decodePixels(dependencies.decode, request.imageUri);
      const input = resizeRgbaToRgbFloat32(
        pixels.rgba,
        pixels.width,
        pixels.height,
        dependencies.preprocessing.width,
        dependencies.preprocessing.height,
      );
      const probabilities = await runModel(dependencies.run, input);
      const prediction = interpretSoftmax(probabilities, dependencies.labels.labels);

      return {
        id: createResultId(),
        cropType: "tomato",
        predictedDiseaseClass: prediction.code,
        confidence: prediction.score,
        modelVersion: dependencies.labels.experiment,
        mode: request.mode,
        timestamp: new Date().toISOString(),
        remedyReference: null,
        isDemo: false,
        status: "model_prediction",
      };
    },
  };
}

async function decodePixels(
  decode: (uri: string) => Promise<PixelImage>,
  uri: string,
): Promise<PixelImage> {
  try {
    return await decode(uri);
  } catch (error) {
    rethrowDiagnosisFailure(error);
    throw new DiagnosisFailure("image_unreadable");
  }
}

async function runModel(
  run: (input: Float32Array) => Promise<Float32Array>,
  input: Float32Array,
): Promise<Float32Array> {
  try {
    return await run(input);
  } catch (error) {
    rethrowDiagnosisFailure(error);
    throw new DiagnosisFailure("inference_failed");
  }
}

function createResultId(): string {
  return `tomato-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}
