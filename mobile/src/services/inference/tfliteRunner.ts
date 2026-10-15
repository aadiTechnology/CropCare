import { File, Paths } from "expo-file-system";
import { Image } from "react-native";
import { loadTensorflowModel, type TfliteModel } from "react-native-fast-tflite";

import modelAsset from "../../../assets/models/tomato/model.tflite";
import { DiagnosisFailure, logDiagnosisDiagnostic, rethrowDiagnosisFailure } from "./DiagnosisFailure";
import { validateModelTensors, type PreprocessingSpec } from "./modelContract";

const MODEL_CACHE_NAME = "cropcare-tomato-model.tflite";

export function createTfliteRunner(
  spec: PreprocessingSpec,
  labelCount: number,
): (input: Float32Array) => Promise<Float32Array> {
  let loading: Promise<TfliteModel> | null = null;

  return async function run(input: Float32Array): Promise<Float32Array> {
    const model = await loadModel();
    const inputTensor = model.inputs[0];
    const outputTensor = model.outputs[0];
    if (!inputTensor || !outputTensor || model.inputs.length !== 1 || model.outputs.length !== 1) {
      logDiagnosisDiagnostic("tensor-count", new DiagnosisFailure("model_unavailable"), {
        inputCount: model.inputs.length,
        outputCount: model.outputs.length,
      });
      throw new DiagnosisFailure("model_unavailable");
    }

    let expected: { inputElements: number; outputElements: number };
    try {
      expected = validateModelTensors(inputTensor, outputTensor, spec, labelCount);
    } catch (error) {
      logDiagnosisDiagnostic("tensor-contract", error, {
        inputName: inputTensor.name,
        inputType: inputTensor.dataType,
        inputShape: shapeText(inputTensor.shape),
        outputName: outputTensor.name,
        outputType: outputTensor.dataType,
        outputShape: shapeText(outputTensor.shape),
        inputLength: input.length,
      });
      throw error;
    }
    logDiagnosisDiagnostic("tensor-contract", null, {
      inputName: inputTensor.name,
      inputType: inputTensor.dataType,
      inputShape: shapeText(inputTensor.shape),
      outputName: outputTensor.name,
      outputType: outputTensor.dataType,
      outputShape: shapeText(outputTensor.shape),
      inputLength: input.length,
    });

    if (input.length !== expected.inputElements) {
      logDiagnosisDiagnostic("input-length", new DiagnosisFailure("inference_failed"), {
        inputLength: input.length,
        expectedLength: expected.inputElements,
      });
      throw new DiagnosisFailure("inference_failed");
    }

    const inputBuffer = copyArrayBuffer(input);
    let outputs: readonly (ArrayBuffer | ArrayBufferView)[];
    try {
      outputs = await model.run([inputBuffer]);
    } catch (error) {
      logDiagnosisDiagnostic("model-run", error);
      throw new DiagnosisFailure("inference_failed");
    }

    const probabilities = readOutputFloats(outputs[0], expected.outputElements);
    logDiagnosisDiagnostic("output", null, outputSummary(probabilities));
    return probabilities;
  };

  function loadModel(): Promise<TfliteModel> {
    if (!loading) {
      loading = openModel().catch((error: unknown) => {
        loading = null;
        logDiagnosisDiagnostic("model-load", error);
        rethrowDiagnosisFailure(error);
        throw new DiagnosisFailure("model_unavailable");
      });
    }
    return loading;
  }
}

/**
 * react-native-fast-tflite 3.0.1 reads require() assets with java.net.URL.
 * On a debug device that URL is the Metro asset (`...?unstable_path=...?...`),
 * and that read fails before TFLite sees the model. Fetch the same asset with
 * the networking stack that already loaded the JS bundle, then open the file.
 */
async function openModel(): Promise<TfliteModel> {
  try {
    return await loadTensorflowModel(modelAsset, []);
  } catch (error) {
    logDiagnosisDiagnostic("model-asset", error);
    const fileUri = await downloadModelToCache();
    return loadTensorflowModel({ url: fileUri }, []);
  }
}

async function downloadModelToCache(): Promise<string> {
  const asset = Image.resolveAssetSource(modelAsset);
  const remoteUri = asset?.uri;
  if (!remoteUri) {
    throw new Error("Tomato model asset URI was empty.");
  }
  if (remoteUri.startsWith("file:")) {
    return remoteUri;
  }

  const response = await fetch(remoteUri);
  if (!response.ok) {
    throw new Error(`Tomato model download failed with status ${response.status}.`);
  }
  const bytes = new Uint8Array(await response.arrayBuffer());
  if (!isTflite(bytes)) {
    throw new Error("Tomato model download was not a TensorFlow Lite file.");
  }

  const file = new File(Paths.cache, MODEL_CACHE_NAME);
  if (file.exists) {
    file.delete();
  }
  file.create({ overwrite: true });
  file.write(bytes);
  logDiagnosisDiagnostic("model-cache", null, { byteLength: bytes.byteLength });
  return file.uri;
}

function isTflite(bytes: Uint8Array): boolean {
  return bytes.length > 8 && bytes[4] === 0x54 && bytes[5] === 0x46 && bytes[6] === 0x4c && bytes[7] === 0x33;
}

function bytesOf(source: ArrayBuffer | ArrayBufferView): Uint8Array {
  if (ArrayBuffer.isView(source)) {
    return new Uint8Array(source.buffer, source.byteOffset, source.byteLength);
  }
  return new Uint8Array(source);
}

function readOutputFloats(buffer: ArrayBuffer | ArrayBufferView | undefined, expectedLength: number): Float32Array {
  if (!buffer) {
    logDiagnosisDiagnostic("output-length", new DiagnosisFailure("inference_failed"), {
      byteLength: 0,
      expectedLength,
    });
    throw new DiagnosisFailure("inference_failed");
  }

  const bytes = bytesOf(buffer);
  const expectedBytes = expectedLength * Float32Array.BYTES_PER_ELEMENT;
  if (bytes.byteLength !== expectedBytes) {
    logDiagnosisDiagnostic("output-length", new DiagnosisFailure("inference_failed"), {
      byteLength: bytes.byteLength,
      expectedLength,
    });
    throw new DiagnosisFailure("inference_failed");
  }

  const copy = new Uint8Array(bytes.byteLength);
  copy.set(bytes);
  return new Float32Array(copy.buffer);
}

function outputSummary(values: Float32Array): Record<string, string | number | null> {
  let sum = 0;
  let min = Number.POSITIVE_INFINITY;
  let max = Number.NEGATIVE_INFINITY;
  let argmax = 0;
  for (let index = 0; index < values.length; index += 1) {
    const value = values[index] ?? Number.NaN;
    sum += value;
    if (value < min) {
      min = value;
    }
    if (value > max) {
      max = value;
      argmax = index;
    }
  }
  return {
    length: values.length,
    sum: Number(sum.toFixed(6)),
    min: Number.isFinite(min) ? Number(min.toFixed(6)) : null,
    max: Number.isFinite(max) ? Number(max.toFixed(6)) : null,
    argmax,
    probabilities: Array.from(values, (value) => value.toFixed(6)).join(","),
  };
}

function shapeText(shape: number[]): string {
  return Array.isArray(shape) ? shape.join("x") : "";
}

function copyArrayBuffer(view: Float32Array): ArrayBuffer {
  const copy = new ArrayBuffer(view.byteLength);
  new Uint8Array(copy).set(new Uint8Array(view.buffer, view.byteOffset, view.byteLength));
  return copy;
}
