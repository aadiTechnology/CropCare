import { collectMessageKeys, resources } from "@/localization/resources";
import { translate } from "@/localization/translate";

describe("localization", () => {
  it("uses the same message keys in English and Marathi", () => {
    expect(collectMessageKeys(resources.en).sort()).toEqual(collectMessageKeys(resources.mr).sort());
  });

  it("defaults the home and diagnosis actions to English", () => {
    expect(translate("en", "home.startDiagnosis")).toBe("Start diagnosis");
    expect(translate("en", "diagnose.takePhoto")).toBe("Take photo");
    expect(translate("en", "diagnose.chooseGallery")).toBe("Choose from gallery");
    expect(translate("en", "nav.history")).toBe("History");
  });

  it("translates the home screen and diagnosis actions into Marathi", () => {
    expect(translate("mr", "home.startDiagnosis")).toBe("निदान सुरू करा");
    expect(translate("mr", "diagnose.takePhoto")).toBe("फोटो काढा");
    expect(translate("mr", "diagnose.chooseGallery")).toBe("गॅलरीमधून निवडा");
    expect(translate("mr", "diagnose.analyze")).toBe("प्रतिमेचे विश्लेषण करा");
    expect(translate("mr", "crops.soybean")).toBe("सोयाबीन");
    expect(translate("mr", "crops.tomato")).toBe("टोमॅटो");
  });
});
