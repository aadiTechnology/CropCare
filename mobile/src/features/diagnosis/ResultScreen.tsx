import { Image, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { Button, Text } from "react-native-paper";

import { DemoBanner } from "@/components/DemoBanner";
import { Screen } from "@/components/Screen";
import { StatusMessage } from "@/components/StatusMessage";
import { useDiagnosisSession } from "@/features/diagnosis/diagnosisSession";
import { useLocalization } from "@/localization/LocalizationProvider";
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

export function ResultScreen() {
  const { t } = useLocalization();
  const router = useRouter();
  const session = useDiagnosisSession();

  if (!session || !session.result.isDemo) {
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
  const modeLabel =
    result.mode === "offline" ? t("result.offlineInactive") : t("result.onlineInactive");

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
