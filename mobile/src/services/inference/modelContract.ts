import { DiagnosisFailure } from "./DiagnosisFailure";

export type ClassLabel = {
  index: number;
  code: string;
  crop: "tomato";
};

export type LabelFile = {
  experiment: string;
  labels: ClassLabel[];
};

export type PreprocessingSpec = {
  height: number;
  width: number;
  channels: number;
  colorOrder: "RGB";
  dtype: "float32";
  valueMin: number;
  valueMax: number;
};

export type TensorDescriptor = {
  dataType: string;
  shape: number[];
};

const TOMATO_CLASS_COUNT = 10;

export function parseLabelFile(value: unknown): LabelFile {
  const record = asRecord(value);
  if (!Array.isArray(record.labels) || record.labels.length !== TOMATO_CLASS_COUNT) {
    throw new DiagnosisFailure("model_unavailable");
  }

  const labels = record.labels.map((item, position) => {
    const label = asRecord(item);
    if (label.index !== position || typeof label.code !== "string" || label.code.length === 0) {
      throw new DiagnosisFailure("model_unavailable");
    }
    if (label.crop !== "tomato") {
      throw new DiagnosisFailure("model_unavailable");
    }
    return { index: position, code: label.code, crop: "tomato" as const };
  });

  if (new Set(labels.map((label) => label.code)).size !== labels.length) {
    throw new DiagnosisFailure("model_unavailable");
  }

  const experiment = typeof record.experiment === "string" ? record.experiment : "plantvillage_tomato";
  return { experiment, labels };
}

export function parsePreprocessingFile(value: unknown): PreprocessingSpec {
  const record = asRecord(value);
  const input = asRecord(record.input);
  const scaling = asRecord(record.internal_scaling);
  const height = input.height;
  const width = input.width;
  const channels = input.channels;
  const valueRange = input.value_range;

  if (
    height !== 224 ||
    width !== 224 ||
    channels !== 3 ||
    input.color_order !== "RGB" ||
    input.dtype !== "float32" ||
    input.resize_method !== "bilinear" ||
    input.resize_applied_outside_model !== true ||
    input.preserve_aspect_ratio !== false ||
    scaling.applied_inside_exported_model !== true ||
    !Array.isArray(valueRange) ||
    valueRange.length !== 2 ||
    valueRange[0] !== 0 ||
    valueRange[1] !== 255
  ) {
    throw new DiagnosisFailure("model_unavailable");
  }

  return {
    height,
    width,
    channels,
    colorOrder: "RGB",
    dtype: "float32",
    valueMin: 0,
    valueMax: 255,
  };
}

export function validateModelTensors(
  input: TensorDescriptor,
  output: TensorDescriptor,
  spec: PreprocessingSpec,
  labelCount: number,
): { inputElements: number; outputElements: number } {
  if (input.dataType !== spec.dtype || output.dataType !== "float32") {
    throw new DiagnosisFailure("model_unavailable");
  }

  const spatial = input.shape.slice(-3);
  const leading = input.shape.slice(0, -3);
  if (
    spatial.length !== 3 ||
    spatial[0] !== spec.height ||
    spatial[1] !== spec.width ||
    spatial[2] !== spec.channels ||
    leading.some((dim) => dim !== 1)
  ) {
    throw new DiagnosisFailure("model_unavailable");
  }

  const inputElements = elementCount(input.shape);
  const outputElements = elementCount(output.shape);
  if (inputElements !== spec.height * spec.width * spec.channels || outputElements !== labelCount) {
    throw new DiagnosisFailure("model_unavailable");
  }

  return { inputElements, outputElements };
}

function elementCount(shape: number[]): number {
  if (shape.length === 0 || shape.some((dim) => !Number.isInteger(dim) || dim <= 0)) {
    throw new DiagnosisFailure("model_unavailable");
  }
  return shape.reduce((product, dim) => product * dim, 1);
}

function asRecord(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object") {
    throw new DiagnosisFailure("model_unavailable");
  }
  return value as Record<string, unknown>;
}
