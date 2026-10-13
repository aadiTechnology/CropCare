import type { DiagnosisRequest, DiagnosisResult } from "@/types";

import type { DiagnosisService } from "./DiagnosisService";

function createPlaceholderId(): string {
  return `placeholder-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export const placeholderDiagnosisService: DiagnosisService = {
  async analyze(request: DiagnosisRequest): Promise<DiagnosisResult> {
    return {
      id: createPlaceholderId(),
      cropType: request.cropType,
      predictedDiseaseClass: null,
      confidence: null,
      modelVersion: null,
      mode: request.mode,
      timestamp: new Date().toISOString(),
      remedyReference: null,
      isDemo: true,
      status: "development_placeholder",
    };
  },
};
