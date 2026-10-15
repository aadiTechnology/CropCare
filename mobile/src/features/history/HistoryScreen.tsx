import { useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";
import { Text } from "react-native-paper";

import { DemoBanner } from "@/components/DemoBanner";
import { Screen } from "@/components/Screen";
import { StatusMessage } from "@/components/StatusMessage";
import { SAMPLE_HISTORY } from "@/features/history/sampleHistory";
import { useLocalization } from "@/localization/LocalizationProvider";
import type { MessageKey } from "@/localization/translate";
import { loadDiagnosisHistoryView } from "@/services/history/diagnosisHistory";
import type { StoredDiagnosis } from "@/services/history/diagnosisHistoryStore";
import { colors } from "@/theme/theme";

type HistoryScreenProps = {
  records?: StoredDiagnosis[];
  unreadableOriginalPresent?: boolean;
  unreadableCopyPreserved?: boolean;
};

function formatModelScore(score: number): string {
  return `${(score * 100).toFixed(1)}% (${score.toFixed(3)})`;
}

function className(code: string, translate: (key: MessageKey) => string): string {
  const key = `classes.${code}` as MessageKey;
  const translated = translate(key);
  return translated === key ? code : translated;
}

export function HistoryScreen({
  records,
  unreadableOriginalPresent = false,
  unreadableCopyPreserved = false,
}: HistoryScreenProps) {
  const { t } = useLocalization();
  const [stored, setStored] = useState<StoredDiagnosis[]>(records ?? []);
  const [originalUnreadable, setOriginalUnreadable] = useState(unreadableOriginalPresent);
  const [copyPreserved, setCopyPreserved] = useState(unreadableCopyPreserved);

  useEffect(() => {
    if (records) {
      setStored(records);
      setOriginalUnreadable(unreadableOriginalPresent);
      setCopyPreserved(unreadableCopyPreserved);
      return;
    }
    let cancelled = false;
    void loadDiagnosisHistoryView().then((view) => {
      if (!cancelled) {
        setStored(view.records);
        setOriginalUnreadable(view.unreadableOriginalPresent);
        setCopyPreserved(view.unreadableCopyPreserved);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [records, unreadableCopyPreserved, unreadableOriginalPresent]);

  return (
    <Screen>
      <Text accessibilityRole="header" variant="titleLarge">
        {t("history.savedHeading")}
      </Text>
      {originalUnreadable ? <StatusMessage message={t("history.unreadableOriginal")} tone="info" /> : null}
      {copyPreserved ? <StatusMessage message={t("history.unreadablePreserved")} tone="info" /> : null}
      {stored.length === 0 ? <StatusMessage message={t("history.empty")} tone="empty" /> : null}
      {stored.map((item) => (
        <View key={item.id} style={styles.card}>
          <Text style={styles.crop} variant="titleLarge">
            {t(item.cropCode === "soybean" ? "crops.soybean" : "crops.tomato")}
          </Text>
          <Text variant="bodyLarge">{className(item.diseaseClassCode, t)}</Text>
          <Text variant="bodyLarge">
            {t("result.classCode")}: {item.diseaseClassCode}
          </Text>
          <Text variant="bodyLarge">
            {t("history.confidence")}: {formatModelScore(item.confidence)}
          </Text>
          <Text variant="bodyLarge">
            {t("history.modelVersion")}: {item.modelVersion}
          </Text>
          <Text variant="bodyLarge">
            {t("result.mode")}: {item.mode === "offline" ? t("result.offlineOnDevice") : t("result.onlineInactive")}
          </Text>
          <Text variant="bodyLarge">
            {t("history.date")}: {item.timestamp}
          </Text>
        </View>
      ))}

      <Text accessibilityRole="header" variant="titleLarge">
        {t("history.sampleHeading")}
      </Text>
      <DemoBanner />
      {SAMPLE_HISTORY.map((item) => (
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
