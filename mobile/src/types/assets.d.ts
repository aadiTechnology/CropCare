declare module "*.tflite" {
  const assetId: number;
  export default assetId;
}

declare module "fast-png" {
  export type DecodedPng = {
    width: number;
    height: number;
    data: Uint8Array | Uint16Array;
    depth: number;
    channels: number;
    palette?: ArrayLike<ArrayLike<number>>;
  };

  export function decode(data: ArrayBufferView | ArrayBuffer): DecodedPng;

  export function encode(image: {
    width: number;
    height: number;
    data: Uint8Array;
    depth?: number;
    channels?: number;
  }): Uint8Array;

  export function convertIndexedToRgb(image: DecodedPng): Uint8Array;
}
