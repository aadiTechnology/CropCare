export const diagnosisFailureCodes = [
  "unsupported_crop",
  "model_unavailable",
  "image_unreadable",
  "inference_failed",
] as const;

export type DiagnosisFailureCode = (typeof diagnosisFailureCodes)[number];

const diagnosisFailureCodeSet = new Set<string>(diagnosisFailureCodes);

/**
 * A diagnosis could not be produced. Callers must show this and must not
 * substitute a made-up class or score.
 */
export class DiagnosisFailure extends Error {
  readonly code: DiagnosisFailureCode;

  constructor(code: DiagnosisFailureCode) {
    super(code);
    this.name = "DiagnosisFailure";
    this.code = code;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * Hermes can fail `instanceof` for `class extends Error`. The code and name
 * still identify a diagnosis failure, including one rethrown across a bundle.
 */
export function diagnosisFailureCode(error: unknown): DiagnosisFailureCode | null {
  if (error instanceof DiagnosisFailure) {
    return error.code;
  }
  if (!error || typeof error !== "object") {
    return null;
  }
  const candidate = error as { name?: unknown; code?: unknown };
  if (
    candidate.name !== "DiagnosisFailure" ||
    typeof candidate.code !== "string" ||
    !diagnosisFailureCodeSet.has(candidate.code)
  ) {
    return null;
  }
  return candidate.code as DiagnosisFailureCode;
}

export function rethrowDiagnosisFailure(error: unknown): void {
  if (diagnosisFailureCode(error) !== null) {
    throw error;
  }
}

type DiagnosticDetails = Record<string, string | number | boolean | null>;

/**
 * Development-only failure context. Callers must pass tensor metadata and
 * error fields, never image bytes, pixel buffers, or photo URIs.
 */
export function logDiagnosisDiagnostic(stage: string, error: unknown, details?: DiagnosticDetails): void {
  if (!isDevelopmentBuild()) {
    return;
  }
  const payload = {
    ...details,
    ...errorFields(error),
  };
  if (error) {
    console.error(`[diagnosis] ${stage}`, payload);
    return;
  }
  console.info(`[diagnosis] ${stage}`, payload);
}

function isDevelopmentBuild(): boolean {
  return (globalThis as { __DEV__?: boolean }).__DEV__ === true;
}

function errorFields(error: unknown): { errorName: string; errorMessage: string; errorCode: string | null } {
  const code = diagnosisFailureCode(error);
  if (error instanceof Error) {
    return {
      errorName: error.name,
      errorMessage: error.message.slice(0, 300),
      errorCode: code,
    };
  }
  if (error && typeof error === "object") {
    const record = error as { name?: unknown; message?: unknown };
    return {
      errorName: typeof record.name === "string" ? record.name : "object",
      errorMessage: typeof record.message === "string" ? record.message.slice(0, 300) : "",
      errorCode: code,
    };
  }
  return {
    errorName: error === null || error === undefined ? "none" : typeof error,
    errorMessage: typeof error === "string" ? error.slice(0, 300) : "",
    errorCode: code,
  };
}
