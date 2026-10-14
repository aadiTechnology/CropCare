import type { DiagnosisRequest, DiagnosisResult } from "@/types";

import type { DiagnosisService } from "./DiagnosisService";

export type { DiagnosisService } from "./DiagnosisService";
export { placeholderDiagnosisService } from "./placeholderDiagnosisService";

export const diagnosisService: DiagnosisService = {
  async analyze(request: DiagnosisRequest): Promise<DiagnosisResult> {
    const module = await import("../inference/productionDiagnosisService");
    return module.productionDiagnosisService.analyze(request);
  },
};
