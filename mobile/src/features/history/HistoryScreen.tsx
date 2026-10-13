import { StyleSheet, View } from "react-native";
import { Text } from "react-native-paper";

import { DemoBanner } from "@/components/DemoBanner";
import { Screen } from "@/components/Screen";
import { StatusMessage } from "@/components/StatusMessage";
import { SAMPLE_HISTORY } from "@/features/history/sampleHistory";
import { useLocalization } from "@/localization/LocalizationProvider";
import { colors } from "@/theme/theme";
import type { DiagnosisHistoryItem } from "@/types";

type HistoryScreenProps = {
  items?: DiagnosisHistoryItem[];
};

export function HistoryScreen({ items = SAMPLE_HISTORY }: HistoryScreenProps) {
  const { t } = useLocalization();

  return (
    <Screen>
      <DemoBanner />
      {items.length === 0 ? <StatusMessage message={t("history.empty")} tone="empty" /> : null}
      {items.map((item) => (
        <View key={item.id} style={styles.card}>
          <Text style={styles.badge} variant="labelLarge">
            {t("common.sample")}
          </Text>
          <Text style={styles.crop} variant="titleLarge">
            {t(item.cropType === "soybean" ? "crops.soybean" : "crops.tomato")}
          </Text>
          <Text variant="bodyLarge">{t("history.sampleLabel")}</Text>
          <Text variant="bodyLarge">
            {t("history.date")}: {item.recordedOn}
          </Text>
        </View>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.outline,
    borderRadius: 14,
    borderWidth: 1,
    padding: 16,
  },
  badge: {
    alignSelf: "flex-start",
    backgroundColor: colors.demoBackground,
    borderRadius: 8,
    color: "#5C4308",
    overflow: "hidden",
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  crop: {
    marginTop: 8,
  },
});
