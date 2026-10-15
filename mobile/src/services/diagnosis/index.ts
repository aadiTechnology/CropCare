import type { DiagnosisRequest, DiagnosisResult } from "@/types";

import { DiagnosisFailure, logDiagnosisDiagnostic } from "../inference/DiagnosisFailure";
import type { DiagnosisService } from "./DiagnosisService";

export type { DiagnosisService } from "./DiagnosisService";
export { placeholderDiagnosisService } from "./placeholderDiagnosisService";

let productionModule: Promise<typeof import("../inference/productionDiagnosisService")> | null = null;

function loadProductionModule(): Promise<typeof import("../inference/productionDiagnosisService")> {
  if (!productionModule) {
    productionModule = import("../inference/productionDiagnosisService").catch((error: unknown) => {
      productionModule = null;
      logDiagnosisDiagnostic("import", error);
      throw new DiagnosisFailure("model_unavailable");
    });
  }
  return productionModule;
}

export const diagnosisService: DiagnosisService = {
  async analyze(request: DiagnosisRequest): Promise<DiagnosisResult> {
    const module = await loadProductionModule();
    return module.productionDiagnosisService.analyze(request);
  },
};
