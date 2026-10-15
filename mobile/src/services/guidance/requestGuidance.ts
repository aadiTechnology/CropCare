/**
 * Read stored guidance from the CropCare API.
 * This does not upload an image and does not run a model.
 */

export const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const GUIDANCE_TIMEOUT_MS = 8000;

export type VerificationStatus = "sample" | "expert_verified";

export type GuidanceText = {
  symptomsEn: string | null;
  symptomsMr: string | null;
  verificationStatus: VerificationStatus;
  source: string | null;
  reviewer: string | null;
  reviewedAt: string | null;
};

export type RemedyGuidance = {
  remedyEn: string | null;
  remedyMr: string | null;
  preventionEn: string | null;
  preventionMr: string | null;
  verificationStatus: VerificationStatus;
  source: string | null;
  reviewer: string | null;
  reviewedAt: string | null;
};

export type StoredGuidance = {
  cropCode: string;
  diseaseCode: string;
  disease: GuidanceText;
  remedies: RemedyGuidance[];
};

export type GuidanceLookup =
  | { status: "ready"; content: StoredGuidance }
  | { status: "unavailable" };

type FetchLike = (input: string, init?: RequestInit) => Promise<Response>;

type GuidanceRequest = {
  cropCode: string;
  diseaseCode: string;
  baseUrl?: string;
  fetchImpl?: FetchLike;
  timeoutMs?: number;
};

export function apiBaseUrl(envValue: string | undefined = process.env.EXPO_PUBLIC_API_BASE_URL): string {
  const trimmed = envValue?.trim();
  if (!trimmed) {
    return DEFAULT_API_BASE_URL;
  }
  return trimmed.replace(/\/+$/, "");
}

export function guidanceRequestUrl(cropCode: string, diseaseCode: string, baseUrl = apiBaseUrl()): string {
  return `${baseUrl}/api/v1/crops/${encodeURIComponent(cropCode)}/diseases/${encodeURIComponent(diseaseCode)}/guidance`;
}

export function parseGuidancePayload(
  value: unknown,
  expected: { cropCode: string; diseaseCode: string },
): StoredGuidance | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const body = value as Record<string, unknown>;
  if (body.data_status !== "database") {
    return null;
  }
  if (body.crop_code !== expected.cropCode || body.disease_code !== expected.diseaseCode) {
    return null;
  }
  const disease = parseDisease(body.disease);
  const remedies = parseRemedies(body.remedies);
  if (!disease || !remedies) {
    return null;
  }
  return {
    cropCode: expected.cropCode,
    diseaseCode: expected.diseaseCode,
    disease,
    remedies,
  };
}

export async function requestStoredGuidance(request: GuidanceRequest): Promise<GuidanceLookup> {
  if (request.cropCode !== "tomato") {
    return { status: "unavailable" };
  }
  const fetchImpl = request.fetchImpl ?? fetch;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), request.timeoutMs ?? GUIDANCE_TIMEOUT_MS);
  try {
    const response = await fetchImpl(guidanceRequestUrl(request.cropCode, request.diseaseCode, request.baseUrl), {
      method: "GET",
      headers: { Accept: "application/json" },
      signal: controller.signal,
    });
    if (!response.ok) {
      return { status: "unavailable" };
    }
    const payload = parseGuidancePayload(await response.json(), {
      cropCode: request.cropCode,
      diseaseCode: request.diseaseCode,
    });
    if (!payload) {
      return { status: "unavailable" };
    }
    return { status: "ready", content: payload };
  } catch {
    return { status: "unavailable" };
  } finally {
    clearTimeout(timer);
  }
}

function parseDisease(value: unknown): GuidanceText | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const row = value as Record<string, unknown>;
  const symptomsEn = optionalText(row.symptoms_en);
  const symptomsMr = optionalText(row.symptoms_mr);
  const source = optionalText(row.source);
  const reviewer = optionalText(row.reviewer);
  const reviewedAt = optionalText(row.reviewed_at);
  const status = row.verification_status;
  if (
    symptomsEn === undefined ||
    symptomsMr === undefined ||
    source === undefined ||
    reviewer === undefined ||
    reviewedAt === undefined ||
    !isStatus(status) ||
    !provenanceIsPublishable(status, source, reviewer, reviewedAt)
  ) {
    return null;
  }
  return {
    symptomsEn,
    symptomsMr,
    verificationStatus: status,
    source: blankToNull(source),
    reviewer: blankToNull(reviewer),
    reviewedAt: blankToNull(reviewedAt),
  };
}

function parseRemedies(value: unknown): RemedyGuidance[] | null {
  if (!Array.isArray(value)) {
    return null;
  }
  const remedies: RemedyGuidance[] = [];
  for (const item of value) {
    if (!item || typeof item !== "object") {
      return null;
    }
    const row = item as Record<string, unknown>;
    const remedyEn = optionalText(row.remedy_en);
    const remedyMr = optionalText(row.remedy_mr);
    const preventionEn = optionalText(row.prevention_en);
    const preventionMr = optionalText(row.prevention_mr);
    const source = optionalText(row.source);
    const reviewer = optionalText(row.reviewer);
    const reviewedAt = optionalText(row.reviewed_at);
    const status = row.verification_status;
    if (
      remedyEn === undefined ||
      remedyMr === undefined ||
      preventionEn === undefined ||
      preventionMr === undefined ||
      source === undefined ||
      reviewer === undefined ||
      reviewedAt === undefined ||
      !isStatus(status) ||
      !provenanceIsPublishable(status, source, reviewer, reviewedAt)
    ) {
      return null;
    }
    remedies.push({
      remedyEn,
      remedyMr,
      preventionEn,
      preventionMr,
      verificationStatus: status,
      source: blankToNull(source),
      reviewer: blankToNull(reviewer),
      reviewedAt: blankToNull(reviewedAt),
    });
  }
  return remedies;
}

function optionalText(value: unknown): string | null | undefined {
  if (value == null) {
    return null;
  }
  if (typeof value !== "string") {
    return undefined;
  }
  return value;
}

function isStatus(value: unknown): value is VerificationStatus {
  return value === "sample" || value === "expert_verified";
}

function provenanceIsPublishable(
  status: VerificationStatus,
  source: string | null,
  reviewer: string | null,
  reviewedAt: string | null,
): boolean {
  if (status === "sample") {
    return true;
  }
  return Boolean(source?.trim() && reviewer?.trim() && reviewedAt?.trim());
}

function blankToNull(value: string | null): string | null {
  if (value == null || value.trim() === "") {
    return null;
  }
  return value;
}
