import type { DiagnosisRequest, DiagnosisResult } from "@/types";

/**
 * Seam for a future on-device model and the FastAPI diagnosis endpoint.
 * Sprint 1 implementations must not invent a disease prediction.
 */
export interface DiagnosisService {
  analyze(request: DiagnosisRequest): Promise<DiagnosisResult>;
}
