const OriginalTextDecoder = globalThis.TextDecoder;

/**
 * fast-png decodes PNG text chunks with TextDecoder("latin1").
 * The Expo winter TextDecoder only accepts UTF-8, so install a small
 * latin1 decoder before that package is loaded.
 */
if (!supportsLatin1(OriginalTextDecoder)) {
  class TextDecoderWithLatin1 {
    private readonly latin1: boolean;
    private readonly inner: TextDecoder | null;

    constructor(label = "utf-8") {
      const normalized = String(label).trim().toLowerCase();
      this.latin1 = normalized === "latin1" || normalized === "iso-8859-1" || normalized === "ascii";
      this.inner = this.latin1 ? null : new OriginalTextDecoder(label);
    }

    decode(input?: BufferSource): string {
      if (this.inner) {
        return this.inner.decode(input);
      }
      const bytes = toBytes(input);
      let text = "";
      for (let index = 0; index < bytes.length; index += 1) {
        text += String.fromCharCode(bytes[index]);
      }
      return text;
    }
  }

  globalThis.TextDecoder = TextDecoderWithLatin1 as unknown as typeof TextDecoder;
}

function supportsLatin1(Decoder: typeof TextDecoder): boolean {
  try {
    new Decoder("latin1");
    return true;
  } catch {
    return false;
  }
}

function toBytes(input: BufferSource | undefined): Uint8Array {
  if (!input) {
    return new Uint8Array();
  }
  if (input instanceof Uint8Array) {
    return input;
  }
  if (ArrayBuffer.isView(input)) {
    return new Uint8Array(input.buffer, input.byteOffset, input.byteLength);
  }
  return new Uint8Array(input);
}
