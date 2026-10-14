import { DiagnosisFailure } from "./DiagnosisFailure";

/**
 * Stretch an RGBA image to the model size with TensorFlow's bilinear rule:
 * half-pixel centers and no align-corners. That is what `tf.image.resize(..., method="bilinear")`
 * used during training.
 *
 * The returned RGB samples stay in the source numeric range. MobileNetV3Small already applies
 * `pixel / 127.5 - 1` inside the exported graph, so this function does not scale them again.
 */
export function resizeRgbaToRgbFloat32(
  rgba: Uint8Array,
  sourceWidth: number,
  sourceHeight: number,
  targetWidth: number,
  targetHeight: number,
): Float32Array {
  if (
    sourceWidth <= 0 ||
    sourceHeight <= 0 ||
    targetWidth <= 0 ||
    targetHeight <= 0 ||
    rgba.length < sourceWidth * sourceHeight * 4
  ) {
    throw new DiagnosisFailure("image_unreadable");
  }

  const output = new Float32Array(targetWidth * targetHeight * 3);
  const xScale = sourceWidth / targetWidth;
  const yScale = sourceHeight / targetHeight;

  for (let y = 0; y < targetHeight; y += 1) {
    const yIn = (y + 0.5) * yScale - 0.5;
    const y0 = Math.floor(yIn);
    const yWeight = yIn - y0;
    const y0Clamped = clamp(y0, 0, sourceHeight - 1);
    const y1Clamped = clamp(y0 + 1, 0, sourceHeight - 1);

    for (let x = 0; x < targetWidth; x += 1) {
      const xIn = (x + 0.5) * xScale - 0.5;
      const x0 = Math.floor(xIn);
      const xWeight = xIn - x0;
      const x0Clamped = clamp(x0, 0, sourceWidth - 1);
      const x1Clamped = clamp(x0 + 1, 0, sourceWidth - 1);
      const destination = (y * targetWidth + x) * 3;

      for (let channel = 0; channel < 3; channel += 1) {
        const topLeft = rgba[(y0Clamped * sourceWidth + x0Clamped) * 4 + channel];
        const topRight = rgba[(y0Clamped * sourceWidth + x1Clamped) * 4 + channel];
        const bottomLeft = rgba[(y1Clamped * sourceWidth + x0Clamped) * 4 + channel];
        const bottomRight = rgba[(y1Clamped * sourceWidth + x1Clamped) * 4 + channel];
        const top = topLeft + (topRight - topLeft) * xWeight;
        const bottom = bottomLeft + (bottomRight - bottomLeft) * xWeight;
        output[destination + channel] = top + (bottom - top) * yWeight;
      }
    }
  }

  return output;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}
