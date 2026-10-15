import { useState } from "react";
import { Image, StyleSheet, View } from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useRouter } from "expo-router";
import { Button, Text } from "react-native-paper";

import { Screen } from "@/components/Screen";
import { StatusMessage } from "@/components/StatusMessage";
import { CropCard } from "@/features/crops/CropCard";
import { setDiagnosisSession } from "@/features/diagnosis/diagnosisSession";
import {
  applyPermissionDenied,
  applyPickerResult,
  emptyImageSelection,
  type ImageSelectionState,
} from "@/features/diagnosis/imageSelection";
import { useLocalization } from "@/localization/LocalizationProvider";
import { routes } from "@/navigation/routes";
import { diagnosisService } from "@/services/diagnosis";
import { saveCompletedDiagnosis } from "@/services/history/diagnosisHistory";
import { requestStoredGuidance } from "@/services/guidance/requestGuidance";
import {
  diagnosisFailureCode,
  logDiagnosisDiagnostic,
  type DiagnosisFailureCode,
} from "@/services/inference/DiagnosisFailure";
import { colors } from "@/theme/theme";
import type { CropType } from "@/types";

type DiagnoseScreenProps = {
  initialCrop?: CropType;
};

export function DiagnoseScreen({ initialCrop = "soybean" }: DiagnoseScreenProps) {
  const { t } = useLocalization();
  const router = useRouter();
  const [crop, setCrop] = useState<CropType>(initialCrop);
  const [selection, setSelection] = useState<ImageSelectionState>(emptyImageSelection);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [failure, setFailure] = useState<DiagnosisFailureCode | "unknown" | null>(null);

  function selectCrop(next: CropType) {
    setCrop(next);
    setFailure(null);
  }

  async function chooseFromGallery() {
    setFailure(null);
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      setSelection((current) => applyPermissionDenied(current));
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images"],
      quality: 0.8,
    });
    setSelection((current) => applyPickerResult(current, result));
  }

  async function takePhoto() {
    setFailure(null);
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      setSelection((current) => applyPermissionDenied(current));
      return;
    }
    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ["images"],
      quality: 0.8,
    });
    setSelection((current) => applyPickerResult(current, result));
  }

  async function analyzeImage() {
    if (!selection.imageUri) {
      return;
    }
    setIsAnalyzing(true);
    setFailure(null);
    try {
      const result = await diagnosisService.analyze({
        cropType: crop,
        imageUri: selection.imageUri,
        mode: "offline",
      });
      const guidance =
        result.status === "model_prediction" && result.predictedDiseaseClass
          ? await requestStoredGuidance({
              cropCode: result.cropType,
              diseaseCode: result.predictedDiseaseClass,
            })
          : { status: "unavailable" as const };
      if (
        result.status === "model_prediction" &&
        result.predictedDiseaseClass &&
        typeof result.confidence === "number" &&
        result.modelVersion
      ) {
        await saveCompletedDiagnosis({
          id: result.id,
          timestamp: result.timestamp,
          cropCode: result.cropType,
          diseaseClassCode: result.predictedDiseaseClass,
          confidence: result.confidence,
          modelVersion: result.modelVersion,
          mode: result.mode,
        });
      }
      setDiagnosisSession({ result, imageUri: selection.imageUri, guidance });
      router.push(routes.result);
    } catch (error) {
      logDiagnosisDiagnostic("analyze", error);
      setFailure(diagnosisFailureCode(error) ?? "unknown");
    } finally {
      setIsAnalyzing(false);
    }
  }

  function failureMessage(code: DiagnosisFailureCode | "unknown"): string {
    switch (code) {
      case "unsupported_crop":
        return t("diagnose.tomatoOnly");
      case "model_unavailable":
        return t("diagnose.modelUnavailable");
      case "image_unreadable":
        return t("diagnose.imageUnreadable");
      case "inference_failed":
        return t("diagnose.inferenceFailed");
      default:
        return t("diagnose.analyzeError");
    }
  }

  return (
    <Screen>
      <Text accessibilityRole="header" style={styles.heading} variant="headlineSmall">
        {t("diagnose.selectCrop")}
      </Text>
      <CropCard crop="soybean" onPress={selectCrop} selected={crop === "soybean"} />
      <CropCard crop="tomato" onPress={selectCrop} selected={crop === "tomato"} />

      <View style={styles.preview}>
        {selection.imageUri ? (
          <Image
            accessibilityLabel={t("diagnose.imagePreview")}
            resizeMode="cover"
            source={{ uri: selection.imageUri }}
            style={styles.image}
          />
        ) : (
          <Text style={styles.placeholder} variant="bodyLarge">
            {t("diagnose.previewPlaceholder")}
          </Text>
        )}
      </View>

      {!selection.imageUri ? <StatusMessage message={t("diagnose.noImage")} tone="empty" /> : null}
      {selection.imageUri ? <StatusMessage message={t("diagnose.imageSelected")} tone="info" /> : null}
      {selection.notice === "cancelled" ? (
        <StatusMessage message={t("diagnose.cancelled")} tone="info" />
      ) : null}
      {selection.notice === "permission_denied" ? (
        <StatusMessage message={t("diagnose.permissionDenied")} tone="error" />
      ) : null}
      {crop === "soybean" && !failure ? (
        <StatusMessage message={t("diagnose.tomatoOnly")} tone="info" />
      ) : null}
      {failure ? <StatusMessage message={failureMessage(failure)} tone="error" /> : null}

      <Button
        contentStyle={styles.buttonContent}
        labelStyle={styles.buttonLabel}
        mode="contained"
        onPress={() => void takePhoto()}
        buttonColor={colors.primary}
        textColor={colors.onPrimary}
      >
        {t("diagnose.takePhoto")}
      </Button>
      <Button
        contentStyle={styles.buttonContent}
        labelStyle={styles.buttonLabel}
        mode="outlined"
        onPress={() => void chooseFromGallery()}
        textColor={colors.primary}
      >
        {t("diagnose.chooseGallery")}
      </Button>
      <Button
        contentStyle={styles.buttonContent}
        disabled={isAnalyzing}
        labelStyle={styles.buttonLabel}
        loading={isAnalyzing}
        mode="contained"
        onPress={() => void analyzeImage()}
        buttonColor={colors.primary}
        textColor={colors.onPrimary}
      >
        {isAnalyzing ? t("common.loading") : t("diagnose.analyze")}
      </Button>
      <Text variant="bodyLarge">{t("diagnose.analyzeHint")}</Text>
    </Screen>
  );
}

const styles = StyleSheet.create({
  heading: {
    fontSize: 26,
    lineHeight: 34,
  },
  preview: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.outline,
    borderRadius: 16,
    borderStyle: "dashed",
    borderWidth: 2,
    height: 220,
    justifyContent: "center",
    overflow: "hidden",
  },
  image: {
    height: "100%",
    width: "100%",
  },
  placeholder: {
    color: colors.onSurfaceVariant,
    fontSize: 18,
    paddingHorizontal: 24,
    textAlign: "center",
  },
  buttonContent: {
    minHeight: 56,
  },
  buttonLabel: {
    fontSize: 18,
  },
});
