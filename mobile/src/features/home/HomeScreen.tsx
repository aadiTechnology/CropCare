import { useState } from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { Button, Text } from "react-native-paper";

import { DemoBanner } from "@/components/DemoBanner";
import { Screen } from "@/components/Screen";
import { CropCard } from "@/features/crops/CropCard";
import { SAMPLE_HISTORY } from "@/features/history/sampleHistory";
import { useLocalization } from "@/localization/LocalizationProvider";
import { routes } from "@/navigation/routes";
import { colors } from "@/theme/theme";
import type { CropType } from "@/types";

export function HomeScreen() {
  const { t } = useLocalization();
  const router = useRouter();
  const [pressedCrop, setPressedCrop] = useState<CropType | null>(null);

  function openDiagnosis(crop?: CropType) {
    if (crop) {
      setPressedCrop(crop);
      router.push({ pathname: routes.diagnose, params: { crop } });
      return;
    }
    router.push(routes.diagnose);
  }

  return (
    <Screen>
      <Text accessibilityRole="header" style={styles.title} variant="headlineMedium">
        {t("appName")}
      </Text>
      <Text style={styles.welcome} variant="bodyLarge">
        {t("home.welcome")}
      </Text>

      <CropCard crop="soybean" onPress={openDiagnosis} selected={pressedCrop === "soybean"} />
      <CropCard crop="tomato" onPress={openDiagnosis} selected={pressedCrop === "tomato"} />

      <Button
        accessibilityLabel={t("home.startDiagnosis")}
        buttonColor={colors.primary}
        contentStyle={styles.buttonContent}
        labelStyle={styles.buttonLabel}
        mode="contained"
        onPress={() => openDiagnosis()}
        textColor={colors.onPrimary}
      >
        {t("home.startDiagnosis")}
      </Button>

      <View style={styles.links}>
        <Button mode="outlined" onPress={() => router.push(routes.history)} textColor={colors.primary}>
          {t("home.openHistory")}
        </Button>
        <Button
          mode="outlined"
          onPress={() => router.push(routes.language)}
          textColor={colors.primary}
        >
          {t("home.openLanguage")}
        </Button>
        <Button mode="outlined" onPress={() => router.push(routes.about)} textColor={colors.primary}>
          {t("home.openAbout")}
        </Button>
      </View>

      <Text accessibilityRole="header" style={styles.sectionTitle} variant="titleLarge">
        {t("home.recent")}
      </Text>
      <DemoBanner />
      <Text variant="bodyLarge">{t("home.sampleNote")}</Text>
      {SAMPLE_HISTORY.map((item) => (
        <View key={item.id} style={styles.record}>
          <Text style={styles.recordTitle} variant="titleMedium">
            {t(item.cropType === "soybean" ? "crops.soybean" : "crops.tomato")}
          </Text>
          <Text variant="bodyLarge">
            {t("common.sample")}: {t("history.sampleLabel")}
          </Text>
          <Text variant="bodyLarge">
            {t("history.date")}: {item.recordedOn}
          </Text>
        </View>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: {
    color: colors.primary,
    fontSize: 34,
    lineHeight: 42,
  },
  welcome: {
    fontSize: 18,
    lineHeight: 28,
  },
  buttonContent: {
    minHeight: 56,
  },
  buttonLabel: {
    fontSize: 18,
  },
  links: {
    gap: 10,
  },
  sectionTitle: {
    fontSize: 24,
    marginTop: 8,
  },
  record: {
    backgroundColor: colors.surface,
    borderColor: colors.outline,
    borderRadius: 14,
    borderWidth: 1,
    padding: 16,
  },
  recordTitle: {
    fontSize: 20,
    marginBottom: 4,
  },
});
