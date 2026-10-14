import { loadTensorflowModel, type TfliteModel } from "react-native-fast-tflite";

import modelAsset from "../../../assets/models/tomato/model.tflite";
import { DiagnosisFailure } from "./DiagnosisFailure";
import { validateModelTensors, type PreprocessingSpec } from "./modelContract";

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
      throw new DiagnosisFailure("model_unavailable");
    }

    const expected = validateModelTensors(inputTensor, outputTensor, spec, labelCount);
    if (input.length !== expected.inputElements) {
      throw new DiagnosisFailure("inference_failed");
    }

    const inputBuffer = copyArrayBuffer(input);
    let outputs: ArrayBuffer[];
    try {
      outputs = await model.run([inputBuffer]);
    } catch (error) {
      console.error("Tomato model inference failed.", error);
      throw new DiagnosisFailure("inference_failed");
    }

    const probabilities = new Float32Array(outputs[0] ?? new ArrayBuffer(0));
    if (probabilities.length !== expected.outputElements) {
      throw new DiagnosisFailure("inference_failed");
    }
    return probabilities;
  };

  function loadModel(): Promise<TfliteModel> {
    if (!loading) {
      loading = openModel().catch((error: unknown) => {
        loading = null;
        console.error("Tomato model could not be loaded.", error);
        if (error instanceof DiagnosisFailure) {
          throw error;
        }
        throw new DiagnosisFailure("model_unavailable");
      });
    }
    return loading;
  }
}

async function openModel(): Promise<TfliteModel> {
  return loadTensorflowModel(modelAsset, []);
}

function copyArrayBuffer(view: Float32Array): ArrayBuffer {
  const copy = new ArrayBuffer(view.byteLength);
  new Uint8Array(copy).set(new Uint8Array(view.buffer, view.byteOffset, view.byteLength));
  return copy;
}
