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
import { placeholderDiagnosisService } from "@/services/diagnosis";
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
  const [analyzeError, setAnalyzeError] = useState(false);

  async function chooseFromGallery() {
    setAnalyzeError(false);
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
    setAnalyzeError(false);
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
    setAnalyzeError(false);
    try {
      const result = await placeholderDiagnosisService.analyze({
        cropType: crop,
        imageUri: selection.imageUri,
        mode: "offline",
      });
      setDiagnosisSession({ result, imageUri: selection.imageUri });
      router.push(routes.result);
    } catch {
      setAnalyzeError(true);
    } finally {
      setIsAnalyzing(false);
    }
  }

  return (
    <Screen>
      <Text accessibilityRole="header" style={styles.heading} variant="headlineSmall">
        {t("diagnose.selectCrop")}
      </Text>
      <CropCard crop="soybean" onPress={setCrop} selected={crop === "soybean"} />
      <CropCard crop="tomato" onPress={setCrop} selected={crop === "tomato"} />

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
      {analyzeError ? <StatusMessage message={t("diagnose.analyzeError")} tone="error" /> : null}

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
