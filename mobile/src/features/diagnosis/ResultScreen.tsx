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
import type { GuidanceLookup, RemedyGuidance, VerificationStatus } from "@/services/guidance/requestGuidance";
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

function textForLanguage(
  language: "en" | "mr",
  english: string | null,
  marathi: string | null,
): string | null {
  const value = language === "mr" ? marathi : english;
  if (value == null || value.trim() === "") {
    return null;
  }
  return value;
}

function statusLabel(
  status: VerificationStatus,
  translate: (key: MessageKey) => string,
): string {
  return status === "expert_verified" ? translate("result.statusExpert") : translate("result.statusSample");
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
        <GuidanceFields guidance={session.guidance} />
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

function GuidanceFields({ guidance }: { guidance: GuidanceLookup | undefined }) {
  const { t, language } = useLocalization();
  if (!guidance || guidance.status !== "ready") {
    return (
      <>
        <StatusMessage message={t("result.guidanceUnavailable")} tone="info" />
        <Field label={t("result.symptoms")} value={t("common.unavailable")} />
        <Field label={t("result.remedy")} value={t("common.unavailable")} />
        <Field label={t("result.prevention")} value={t("common.unavailable")} />
      </>
    );
  }

  const { disease, remedies } = guidance.content;
  const symptoms = textForLanguage(language, disease.symptomsEn, disease.symptomsMr);
  const sampleRemedy = remedies.some((remedy) => remedy.verificationStatus === "sample");
  return (
    <>
      <StatusMessage
        message={disease.verificationStatus === "expert_verified" ? t("result.guidanceVerified") : t("result.guidanceSample")}
        tone="info"
      />
      {disease.verificationStatus === "expert_verified" && sampleRemedy ? (
        <StatusMessage message={t("result.guidanceSample")} tone="info" />
      ) : null}
      <Field label={t("result.verificationStatus")} value={statusLabel(disease.verificationStatus, t)} />
      <ProvenanceFields source={disease.source} reviewer={disease.reviewer} reviewedAt={disease.reviewedAt} />
      <Field label={t("result.symptoms")} value={symptoms ?? t("common.unavailable")} />
      {remedies.length === 0 ? (
        <>
          <Field label={t("result.remedy")} value={t("common.unavailable")} />
          <Field label={t("result.prevention")} value={t("common.unavailable")} />
        </>
      ) : (
        remedies.map((remedy, index) => <RemedyFields key={`${remedy.verificationStatus}-${index}`} remedy={remedy} />)
      )}
    </>
  );
}

function RemedyFields({ remedy }: { remedy: RemedyGuidance }) {
  const { t, language } = useLocalization();
  const remedyText = textForLanguage(language, remedy.remedyEn, remedy.remedyMr);
  const preventionText = textForLanguage(language, remedy.preventionEn, remedy.preventionMr);
  return (
    <>
      <Field label={t("result.verificationStatus")} value={statusLabel(remedy.verificationStatus, t)} />
      <ProvenanceFields source={remedy.source} reviewer={remedy.reviewer} reviewedAt={remedy.reviewedAt} />
      <Field label={t("result.remedy")} value={remedyText ?? t("common.unavailable")} />
      <Field label={t("result.prevention")} value={preventionText ?? t("common.unavailable")} />
    </>
  );
}

function ProvenanceFields({
  source,
  reviewer,
  reviewedAt,
}: {
  source: string | null;
  reviewer: string | null;
  reviewedAt: string | null;
}) {
  const { t } = useLocalization();
  return (
    <>
      {source ? <Field label={t("result.source")} value={source} /> : null}
      {reviewer ? <Field label={t("result.reviewer")} value={reviewer} /> : null}
      {reviewedAt ? <Field label={t("result.reviewedAt")} value={reviewedAt} /> : null}
    </>
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
