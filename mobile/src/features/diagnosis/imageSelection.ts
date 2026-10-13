export type ImageSelectionState = {
  imageUri: string | null;
  notice: "none" | "cancelled" | "permission_denied";
};

export type ImagePickerResult = {
  canceled: boolean;
  assets?: { uri: string }[] | null;
};

export const emptyImageSelection: ImageSelectionState = {
  imageUri: null,
  notice: "none",
};

export function applyPickerResult(
  current: ImageSelectionState,
  result: ImagePickerResult,
): ImageSelectionState {
  const uri = result.canceled ? null : result.assets?.[0]?.uri;
  if (!uri) {
    return { imageUri: current.imageUri, notice: "cancelled" };
  }
  return { imageUri: uri, notice: "none" };
}

export function applyPermissionDenied(current: ImageSelectionState): ImageSelectionState {
  return { imageUri: current.imageUri, notice: "permission_denied" };
}
