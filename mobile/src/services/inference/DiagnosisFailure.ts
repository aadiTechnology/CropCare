export const diagnosisFailureCodes = [
  "unsupported_crop",
  "model_unavailable",
  "image_unreadable",
  "inference_failed",
] as const;

export type DiagnosisFailureCode = (typeof diagnosisFailureCodes)[number];

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
  }
}
