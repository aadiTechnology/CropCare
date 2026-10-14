import "./latin1TextDecoder";
import { convertIndexedToRgb, decode as decodePng, type DecodedPng } from "fast-png";
import { decode as decodeJpeg } from "jpeg-js";

import { DiagnosisFailure } from "./DiagnosisFailure";

export type PixelImage = {
  width: number;
  height: number;
  rgba: Uint8Array;
};

/**
 * Decode encoded JPEG or PNG bytes into an RGBA pixel buffer.
 * Returns null for any other format so the caller can transcode it.
 * Encoded bytes are not a model input.
 */
export function decodeImageBytes(bytes: Uint8Array): PixelImage | null {
  try {
    if (isJpeg(bytes)) {
      return decodeJpegBytes(bytes);
    }
    if (isPng(bytes)) {
      return decodePngBytes(bytes);
    }
    return null;
  } catch (error) {
    if (error instanceof DiagnosisFailure) {
      throw error;
    }
    return null;
  }
}

export function readJpegOrientation(bytes: Uint8Array): number {
  if (!isJpeg(bytes)) {
    return 1;
  }
  let offset = 2;
  while (offset + 4 < bytes.length) {
    if (bytes[offset] !== 0xff) {
      return 1;
    }
    const marker = bytes[offset + 1];
    if (marker === 0xda || marker === 0xd9) {
      return 1;
    }
    const segmentLength = (bytes[offset + 2] << 8) | bytes[offset + 3];
    if (segmentLength < 2 || offset + 2 + segmentLength > bytes.length) {
      return 1;
    }
    if (marker === 0xe1) {
      const payload = offset + 4;
      const isExif =
        bytes[payload] === 0x45 &&
        bytes[payload + 1] === 0x78 &&
        bytes[payload + 2] === 0x69 &&
        bytes[payload + 3] === 0x66 &&
        bytes[payload + 4] === 0 &&
        bytes[payload + 5] === 0;
      if (isExif) {
        return readTiffOrientation(bytes, payload + 6, offset + 2 + segmentLength);
      }
    }
    offset += 2 + segmentLength;
  }
  return 1;
}

function decodeJpegBytes(bytes: Uint8Array): PixelImage {
  const decoded = decodeJpeg(bytes, { useTArray: true, formatAsRGBA: true });
  const oriented = applyExifOrientation(
    { width: decoded.width, height: decoded.height, rgba: decoded.data },
    readJpegOrientation(bytes),
  );
  assertPixelImage(oriented);
  return oriented;
}

function decodePngBytes(bytes: Uint8Array): PixelImage {
  const decoded = decodePng(bytes);
  if (decoded.palette) {
    const expanded = convertIndexedToRgb(decoded);
    const channels = decoded.palette[0]?.length === 4 ? 4 : 3;
    return pngToRgba({ ...decoded, data: expanded, channels, depth: 8 });
  }
  return pngToRgba(decoded);
}

function pngToRgba(decoded: DecodedPng): PixelImage {
  if (decoded.depth !== 8 || !(decoded.data instanceof Uint8Array)) {
    throw new DiagnosisFailure("image_unreadable");
  }
  const { width, height, channels, data } = decoded;
  const pixelCount = width * height;
  if (width <= 0 || height <= 0 || data.length < pixelCount * channels) {
    throw new DiagnosisFailure("image_unreadable");
  }
  const rgba = new Uint8Array(pixelCount * 4);
  if (channels === 4) {
    rgba.set(data.subarray(0, pixelCount * 4));
  } else if (channels === 3) {
    for (let pixel = 0; pixel < pixelCount; pixel += 1) {
      const source = pixel * 3;
      const destination = pixel * 4;
      rgba[destination] = data[source];
      rgba[destination + 1] = data[source + 1];
      rgba[destination + 2] = data[source + 2];
      rgba[destination + 3] = 255;
    }
  } else if (channels === 2) {
    for (let pixel = 0; pixel < pixelCount; pixel += 1) {
      const source = pixel * 2;
      const destination = pixel * 4;
      rgba[destination] = data[source];
      rgba[destination + 1] = data[source];
      rgba[destination + 2] = data[source];
      rgba[destination + 3] = data[source + 1];
    }
  } else if (channels === 1) {
    for (let pixel = 0; pixel < pixelCount; pixel += 1) {
      const destination = pixel * 4;
      rgba[destination] = data[pixel];
      rgba[destination + 1] = data[pixel];
      rgba[destination + 2] = data[pixel];
      rgba[destination + 3] = 255;
    }
  } else {
    throw new DiagnosisFailure("image_unreadable");
  }
  return { width, height, rgba };
}

export function applyExifOrientation(image: PixelImage, orientation: number): PixelImage {
  if (orientation === 1) {
    return image;
  }
  const { width, height, rgba } = image;
  const swapped = orientation >= 5;
  const nextWidth = swapped ? height : width;
  const nextHeight = swapped ? width : height;
  const next = new Uint8Array(nextWidth * nextHeight * 4);

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const mapped = mapOrientedPixel(orientation, x, y, width, height);
      const source = (y * width + x) * 4;
      const destination = (mapped.y * nextWidth + mapped.x) * 4;
      next[destination] = rgba[source];
      next[destination + 1] = rgba[source + 1];
      next[destination + 2] = rgba[source + 2];
      next[destination + 3] = rgba[source + 3];
    }
  }

  return { width: nextWidth, height: nextHeight, rgba: next };
}

function mapOrientedPixel(
  orientation: number,
  x: number,
  y: number,
  width: number,
  height: number,
): { x: number; y: number } {
  switch (orientation) {
    case 2:
      return { x: width - 1 - x, y };
    case 3:
      return { x: width - 1 - x, y: height - 1 - y };
    case 4:
      return { x, y: height - 1 - y };
    case 5:
      return { x: y, y: x };
    case 6:
      return { x: height - 1 - y, y: x };
    case 7:
      return { x: height - 1 - y, y: width - 1 - x };
    case 8:
      return { x: y, y: width - 1 - x };
    default:
      return { x, y };
  }
}

function readTiffOrientation(bytes: Uint8Array, tiffStart: number, segmentEnd: number): number {
  if (tiffStart + 8 > segmentEnd) {
    return 1;
  }
  const little = bytes[tiffStart] === 0x49 && bytes[tiffStart + 1] === 0x49;
  const big = bytes[tiffStart] === 0x4d && bytes[tiffStart + 1] === 0x4d;
  if (!little && !big) {
    return 1;
  }
  const read16 = (position: number) =>
    little ? bytes[position] | (bytes[position + 1] << 8) : (bytes[position] << 8) | bytes[position + 1];
  const read32 = (position: number) =>
    little
      ? bytes[position] |
        (bytes[position + 1] << 8) |
        (bytes[position + 2] << 16) |
        (bytes[position + 3] << 24)
      : (bytes[position] << 24) |
        (bytes[position + 1] << 16) |
        (bytes[position + 2] << 8) |
        bytes[position + 3];
  const ifd = tiffStart + read32(tiffStart + 4);
  if (ifd + 2 > segmentEnd) {
    return 1;
  }
  const entries = read16(ifd);
  for (let index = 0; index < entries; index += 1) {
    const entry = ifd + 2 + index * 12;
    if (entry + 12 > segmentEnd) {
      return 1;
    }
    if (read16(entry) === 0x0112) {
      const value = read16(entry + 8);
      return value >= 1 && value <= 8 ? value : 1;
    }
  }
  return 1;
}

function assertPixelImage(image: PixelImage): void {
  if (image.width <= 0 || image.height <= 0 || image.rgba.length < image.width * image.height * 4) {
    throw new DiagnosisFailure("image_unreadable");
  }
}

function isJpeg(bytes: Uint8Array): boolean {
  return bytes.length > 3 && bytes[0] === 0xff && bytes[1] === 0xd8;
}

function isPng(bytes: Uint8Array): boolean {
  return (
    bytes.length > 8 &&
    bytes[0] === 0x89 &&
    bytes[1] === 0x50 &&
    bytes[2] === 0x4e &&
    bytes[3] === 0x47
  );
}
