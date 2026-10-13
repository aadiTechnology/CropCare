import { StyleSheet, View } from "react-native";
import { Text } from "react-native-paper";

import { useLocalization } from "@/localization/LocalizationProvider";
import { colors } from "@/theme/theme";

export function DemoBanner() {
  const { t } = useLocalization();

  return (
    <View accessibilityRole="text" style={styles.banner}>
      <Text style={styles.label} variant="titleMedium">
        {t("common.demoBanner")}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: colors.demoBackground,
    borderColor: colors.demoBorder,
    borderRadius: 12,
    borderWidth: 2,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  label: {
    color: "#5C4308",
    fontSize: 18,
    lineHeight: 26,
  },
});
