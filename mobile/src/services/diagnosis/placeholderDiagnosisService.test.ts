import { placeholderDiagnosisService } from "@/services/diagnosis";

describe("placeholder diagnosis service", () => {
  it("does not invent a disease, confidence, or remedy", async () => {
    const result = await placeholderDiagnosisService.analyze({
      cropType: "tomato",
      imageUri: "file:///leaf.jpg",
      mode: "offline",
    });

    expect(result.cropType).toBe("tomato");
    expect(result.mode).toBe("offline");
    expect(result.predictedDiseaseClass).toBeNull();
    expect(result.confidence).toBeNull();
    expect(result.modelVersion).toBeNull();
    expect(result.remedyReference).toBeNull();
    expect(result.isDemo).toBe(true);
    expect(result.status).toBe("development_placeholder");
    expect(result.id.startsWith("placeholder-")).toBe(true);
  });
});
