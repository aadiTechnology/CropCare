import { File } from "expo-file-system";
import { ImageManipulator, SaveFormat } from "expo-image-manipulator";

import { DiagnosisFailure, logDiagnosisDiagnostic, rethrowDiagnosisFailure } from "./DiagnosisFailure";
import { decodeImageBytes, type PixelImage } from "./decodeImageBytes";

/**
 * Read a picked photo into RGBA pixels.
 * JPEG and PNG are decoded in JavaScript. Other formats are converted to PNG
 * by Expo Image Manipulator first, because the TensorFlow Lite model cannot
 * accept encoded image bytes.
 */
export async function readImagePixels(uri: string): Promise<PixelImage> {
  const direct = await tryDecodeUri(uri);
  if (direct) {
    return direct;
  }

  try {
    const context = ImageManipulator.manipulate(uri);
    const rendered = await context.renderAsync();
    const saved = await rendered.saveAsync({ compress: 1, format: SaveFormat.PNG });
    const transcoded = await tryDecodeUri(saved.uri);
    if (!transcoded) {
      throw new DiagnosisFailure("image_unreadable");
    }
    return transcoded;
  } catch (error) {
    rethrowDiagnosisFailure(error);
    logDiagnosisDiagnostic("image-decode", error);
    throw new DiagnosisFailure("image_unreadable");
  }
}

async function tryDecodeUri(uri: string): Promise<PixelImage | null> {
  try {
    const bytes = await new File(uri).bytes();
    return decodeImageBytes(bytes);
  } catch (error) {
    rethrowDiagnosisFailure(error);
    return null;
  }
}
