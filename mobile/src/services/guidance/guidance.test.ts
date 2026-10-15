import {
  apiBaseUrl,
  DEFAULT_API_BASE_URL,
  guidanceRequestUrl,
  parseGuidancePayload,
  requestStoredGuidance,
  type StoredGuidance,
} from "./requestGuidance";

const reviewed: StoredGuidance = {
  cropCode: "tomato",
  diseaseCode: "tomato_healthy",
  disease: {
    symptomsEn: "stored-symptom-en",
    symptomsMr: null,
    verificationStatus: "expert_verified",
    source: "test-citation",
    reviewer: "test-reviewer",
    reviewedAt: "2026-10-15T04:30:00Z",
  },
  remedies: [
    {
      remedyEn: null,
      remedyMr: "stored-remedy-mr",
      preventionEn: "stored-prevention-en",
      preventionMr: null,
      verificationStatus: "sample",
      source: null,
      reviewer: null,
      reviewedAt: null,
    },
  ],
};

function payloadFrom(content: StoredGuidance): Record<string, unknown> {
  return {
    data_status: "database",
    disclaimer: "stored disclaimer",
    crop_code: content.cropCode,
    disease_code: content.diseaseCode,
    disease: {
      code: content.diseaseCode,
      name_en: "Stored disease",
      name_mr: "साठवलेला रोग",
      symptoms_en: content.disease.symptomsEn,
      symptoms_mr: content.disease.symptomsMr,
      verification_status: content.disease.verificationStatus,
      source: content.disease.source,
      reviewer: content.disease.reviewer,
      reviewed_at: content.disease.reviewedAt,
    },
    remedies: content.remedies.map((remedy) => ({
      remedy_en: remedy.remedyEn,
      remedy_mr: remedy.remedyMr,
      prevention_en: remedy.preventionEn,
      prevention_mr: remedy.preventionMr,
      verification_status: remedy.verificationStatus,
      source: remedy.source,
      reviewer: remedy.reviewer,
      reviewed_at: remedy.reviewedAt,
    })),
  };
}

function jsonResponse(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

describe("guidance client", () => {
  it("uses the local API address when no override is set", () => {
    expect(apiBaseUrl(undefined)).toBe(DEFAULT_API_BASE_URL);
    expect(apiBaseUrl("  ")).toBe(DEFAULT_API_BASE_URL);
    expect(apiBaseUrl("http://10.0.2.2:8000/")).toBe("http://10.0.2.2:8000");
    expect(guidanceRequestUrl("tomato", "tomato_healthy", "http://127.0.0.1:8000")).toBe(
      "http://127.0.0.1:8000/api/v1/crops/tomato/diseases/tomato_healthy/guidance",
    );
  });

  it("keeps a reviewed payload, including a missing translation", () => {
    expect(parseGuidancePayload(payloadFrom(reviewed), { cropCode: "tomato", diseaseCode: "tomato_healthy" })).toEqual(
      reviewed,
    );
  });

  it("rejects expert verification that has no provenance", () => {
    const body = payloadFrom(reviewed);
    const disease = body.disease as Record<string, unknown>;
    disease.source = "   ";
    expect(parseGuidancePayload(body, { cropCode: "tomato", diseaseCode: "tomato_healthy" })).toBeNull();
  });

  it("rejects an unknown verification status and a mismatched class", () => {
    const unknown = payloadFrom(reviewed);
    (unknown.disease as Record<string, unknown>).verification_status = "draft";
    expect(parseGuidancePayload(unknown, { cropCode: "tomato", diseaseCode: "tomato_healthy" })).toBeNull();
    expect(
      parseGuidancePayload(payloadFrom(reviewed), { cropCode: "tomato", diseaseCode: "tomato_early_blight" }),
    ).toBeNull();
  });

  it("returns stored guidance from a successful response", async () => {
    const fetchImpl = jest.fn(async () => jsonResponse(200, payloadFrom(reviewed)));
    await expect(
      requestStoredGuidance({
        cropCode: "tomato",
        diseaseCode: "tomato_healthy",
        baseUrl: "http://127.0.0.1:8000",
        fetchImpl,
      }),
    ).resolves.toEqual({ status: "ready", content: reviewed });
    expect(fetchImpl).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/crops/tomato/diseases/tomato_healthy/guidance",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("treats not-found, network failure, timeout, and malformed JSON as no guidance", async () => {
    const notFound = jest.fn(async () => jsonResponse(404, { detail: "No stored guidance for this class." }));
    await expect(
      requestStoredGuidance({ cropCode: "tomato", diseaseCode: "tomato_healthy", fetchImpl: notFound }),
    ).resolves.toEqual({ status: "unavailable" });

    const failed = jest.fn(async () => {
      throw new Error("network down");
    });
    await expect(
      requestStoredGuidance({ cropCode: "tomato", diseaseCode: "tomato_healthy", fetchImpl: failed }),
    ).resolves.toEqual({ status: "unavailable" });

    const hung = jest.fn((_url: string, init?: RequestInit) => {
      return new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => reject(new Error("aborted")));
      });
    });
    await expect(
      requestStoredGuidance({
        cropCode: "tomato",
        diseaseCode: "tomato_healthy",
        fetchImpl: hung,
        timeoutMs: 5,
      }),
    ).resolves.toEqual({ status: "unavailable" });

    const malformed = jest.fn(async () => jsonResponse(200, { data_status: "database", disease: { symptoms_en: 1 } }));
    await expect(
      requestStoredGuidance({ cropCode: "tomato", diseaseCode: "tomato_healthy", fetchImpl: malformed }),
    ).resolves.toEqual({ status: "unavailable" });
  });

  it("does not call the API for soybean", async () => {
    const fetchImpl = jest.fn();
    await expect(
      requestStoredGuidance({ cropCode: "soybean", diseaseCode: "tomato_healthy", fetchImpl }),
    ).resolves.toEqual({ status: "unavailable" });
    expect(fetchImpl).not.toHaveBeenCalled();
  });
});
