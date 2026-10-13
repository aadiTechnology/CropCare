export type CropType = "soybean" | "tomato";

export type DiagnosisMode = "offline" | "online";

export type VerificationStatus = "sample" | "expert_verified";

/**
 * Result contract for a future diagnosis.
 * Sprint 1 leaves prediction fields empty and marks the record as demo data.
 */
export interface DiagnosisResult {
  id: string;
  cropType: CropType;
  predictedDiseaseClass: string | null;
  confidence: number | null;
  modelVersion: string | null;
  mode: DiagnosisMode;
  timestamp: string;
  remedyReference: string | null;
  isDemo: boolean;
  status: "development_placeholder";
}

export interface DiagnosisRequest {
  cropType: CropType;
  imageUri: string;
  mode: DiagnosisMode;
}

export interface DiseaseInformation {
  id: string;
  cropType: CropType;
  code: string;
  nameEn: string;
  nameMr: string;
  symptomsEn: string | null;
  symptomsMr: string | null;
  verificationStatus: VerificationStatus;
}

export interface RemedyInformation {
  id: string;
  diseaseId: string;
  remedyEn: string | null;
  remedyMr: string | null;
  preventionEn: string | null;
  preventionMr: string | null;
  verificationStatus: VerificationStatus;
}

export interface DiagnosisHistoryItem {
  id: string;
  cropType: CropType;
  recordedOn: string;
  isDemo: true;
}

export function isCropType(value: string | undefined): value is CropType {
  return value === "soybean" || value === "tomato";
}
