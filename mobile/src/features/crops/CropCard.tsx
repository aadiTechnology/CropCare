import { Pressable, StyleSheet } from "react-native";
import { Text } from "react-native-paper";

import { useLocalization } from "@/localization/LocalizationProvider";
import { colors } from "@/theme/theme";
import type { CropType } from "@/types";

type CropCardProps = {
  crop: CropType;
  selected?: boolean;
  onPress: (crop: CropType) => void;
};

export function CropCard({ crop, selected = false, onPress }: CropCardProps) {
  const { t } = useLocalization();
  const label = t(crop === "soybean" ? "crops.soybean" : "crops.tomato");

  return (
    <Pressable
      accessibilityLabel={label}
      accessibilityRole="button"
      accessibilityState={{ selected }}
      onPress={() => onPress(crop)}
      style={[styles.card, selected ? styles.selected : null]}
    >
      <Text style={styles.title} variant="headlineSmall">
        {label}
      </Text>
      {selected ? (
        <Text style={styles.selectedLabel} variant="bodyLarge">
          {t("diagnose.selected")}
        </Text>
      ) : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.outline,
    borderRadius: 16,
    borderWidth: 2,
    minHeight: 96,
    justifyContent: "center",
    paddingHorizontal: 20,
    paddingVertical: 18,
  },
  selected: {
    backgroundColor: colors.primaryContainer,
    borderColor: colors.primary,
  },
  title: {
    color: colors.onSurface,
    fontSize: 28,
    lineHeight: 36,
  },
  selectedLabel: {
    color: colors.primary,
    marginTop: 4,
  },
});
