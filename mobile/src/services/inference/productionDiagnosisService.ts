import labelsJson from "../../../assets/models/tomato/labels.json";
import preprocessingJson from "../../../assets/models/tomato/preprocessing.json";

import { parseLabelFile, parsePreprocessingFile } from "./modelContract";
import { readImagePixels } from "./readImagePixels";
import { createTomatoDiagnosisService } from "./tomatoDiagnosisService";
import { createTfliteRunner } from "./tfliteRunner";

const labels = parseLabelFile(labelsJson);
const preprocessing = parsePreprocessingFile(preprocessingJson);

/**
 * On-device tomato classifier.
 * react-native-fast-tflite is a native module, so this service runs in an
 * Expo development build. Expo Go does not include it.
 * The CPU delegate is used. Pixel values stay in 0–255; model scaling is internal.
 */
export const productionDiagnosisService = createTomatoDiagnosisService({
  labels,
  preprocessing,
  decode: readImagePixels,
  run: createTfliteRunner(preprocessing, labels.labels.length),
});
