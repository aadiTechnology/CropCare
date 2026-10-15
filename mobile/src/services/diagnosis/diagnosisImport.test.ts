jest.mock("../inference/productionDiagnosisService", () => {
  throw new Error("Failed to get NitroModules");
});

import { diagnosisService } from "@/services/diagnosis";

describe("diagnosis service import", () => {
  it("reports model_unavailable when the on-device inference module fails to load", async () => {
    await expect(
      diagnosisService.analyze({
        cropType: "tomato",
        imageUri: "file:///leaf.jpg",
        mode: "offline",
      }),
    ).rejects.toMatchObject({
      name: "DiagnosisFailure",
      code: "model_unavailable",
    });
  });
});
