import {
  applyPermissionDenied,
  applyPickerResult,
  emptyImageSelection,
} from "@/features/diagnosis/imageSelection";

describe("image selection", () => {
  it("keeps the empty state and records cancellation", () => {
    const next = applyPickerResult(emptyImageSelection, { canceled: true, assets: null });

    expect(next).toEqual({ imageUri: null, notice: "cancelled" });
  });

  it("stores the selected image uri", () => {
    const next = applyPickerResult(emptyImageSelection, {
      canceled: false,
      assets: [{ uri: "file:///leaf.jpg" }],
    });

    expect(next).toEqual({ imageUri: "file:///leaf.jpg", notice: "none" });
  });

  it("keeps an existing photo when a later selection is cancelled", () => {
    const selected = applyPickerResult(emptyImageSelection, {
      canceled: false,
      assets: [{ uri: "file:///leaf.jpg" }],
    });

    expect(applyPickerResult(selected, { canceled: true })).toEqual({
      imageUri: "file:///leaf.jpg",
      notice: "cancelled",
    });
  });

  it("records a denied permission without clearing a selected photo", () => {
    const selected = { imageUri: "file:///leaf.jpg", notice: "none" as const };

    expect(applyPermissionDenied(selected)).toEqual({
      imageUri: "file:///leaf.jpg",
      notice: "permission_denied",
    });
  });
});
