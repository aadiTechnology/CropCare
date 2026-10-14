import { Image, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { Button, Text } from "react-native-paper";

import { DemoBanner } from "@/components/DemoBanner";
import { Screen } from "@/components/Screen";
import { StatusMessage } from "@/components/StatusMessage";
import { useDiagnosisSession } from "@/features/diagnosis/diagnosisSession";
import { useLocalization } from "@/localization/LocalizationProvider";
import type { MessageKey } from "@/localization/translate";
import { routes } from "@/navigation/routes";
import { colors } from "@/theme/theme";

function Field({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel} variant="titleMedium">
        {label}
      </Text>
      <Text variant="bodyLarge">{value}</Text>
    </View>
  );
}

function formatModelScore(score: number): string {
  return `${(score * 100).toFixed(1)}% (${score.toFixed(3)})`;
}

function className(code: string, translate: (key: MessageKey) => string): string {
  const key = `classes.${code}` as MessageKey;
  const translated = translate(key);
  return translated === key ? code : translated;
}

export function ResultScreen() {
  const { t } = useLocalization();
  const router = useRouter();
  const session = useDiagnosisSession();

  if (!session) {
    return (
      <Screen>
        <StatusMessage message={t("result.empty")} tone="empty" />
        <Button mode="contained" onPress={() => router.push(routes.diagnose)} buttonColor={colors.primary}>
          {t("result.emptyAction")}
        </Button>
      </Screen>
    );
  }

  const { result, imageUri } = session;
  const cropLabel = t(result.cropType === "soybean" ? "crops.soybean" : "crops.tomato");

  if (
    result.status === "model_prediction" &&
    result.predictedDiseaseClass &&
    typeof result.confidence === "number"
  ) {
    return (
      <Screen>
        <StatusMessage message={t("result.modelDisclaimer")} tone="info" />
        <Image
          accessibilityLabel={t("diagnose.imagePreview")}
          resizeMode="cover"
          source={{ uri: imageUri }}
          style={styles.image}
        />
        <Field label={t("result.crop")} value={cropLabel} />
        <Field
          label={t("result.predictedClass")}
          value={className(result.predictedDiseaseClass, t)}
        />
        <Field label={t("result.classCode")} value={result.predictedDiseaseClass} />
        <Field label={t("result.confidence")} value={formatModelScore(result.confidence)} />
        <StatusMessage message={t("result.confidenceNote")} tone="info" />
        <Field label={t("result.modelVersion")} value={result.modelVersion ?? t("common.unavailable")} />
        <Field label={t("result.mode")} value={t("result.offlineOnDevice")} />
        <Field label={t("result.time")} value={result.timestamp} />
        <Field label={t("result.symptoms")} value={t("result.placeholderBody")} />
        <Field label={t("result.remedy")} value={t("result.placeholderBody")} />
        <Field label={t("result.prevention")} value={t("result.placeholderBody")} />
      </Screen>
    );
  }

  if (!result.isDemo) {
    return (
      <Screen>
        <StatusMessage message={t("result.empty")} tone="empty" />
        <Button mode="contained" onPress={() => router.push(routes.diagnose)} buttonColor={colors.primary}>
          {t("result.emptyAction")}
        </Button>
      </Screen>
    );
  }

  const modeLabel = result.mode === "offline" ? t("result.offlineInactive") : t("result.onlineInactive");

  return (
    <Screen>
      <DemoBanner />
      <StatusMessage message={t("result.disclaimer")} tone="info" />
      <Image
        accessibilityLabel={t("diagnose.imagePreview")}
        resizeMode="cover"
        source={{ uri: imageUri }}
        style={styles.image}
      />
      <Field label={t("result.crop")} value={cropLabel} />
      <Field label={t("result.disease")} value={t("common.unavailable")} />
      <Field label={t("result.confidence")} value={t("common.unavailable")} />
      <Field label={t("result.modelVersion")} value={t("common.unavailable")} />
      <Field label={t("result.mode")} value={modeLabel} />
      <Field label={t("result.time")} value={result.timestamp} />
      <Field label={t("result.symptoms")} value={t("result.placeholderBody")} />
      <Field label={t("result.remedy")} value={t("result.placeholderBody")} />
      <Field label={t("result.prevention")} value={t("result.placeholderBody")} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  image: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    height: 220,
    width: "100%",
  },
  field: {
    backgroundColor: colors.surface,
    borderColor: colors.outline,
    borderRadius: 14,
    borderWidth: 1,
    padding: 16,
  },
  fieldLabel: {
    color: colors.primary,
    marginBottom: 4,
  },
});
