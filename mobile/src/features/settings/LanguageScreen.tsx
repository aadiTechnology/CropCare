import { Pressable, StyleSheet, View } from "react-native";
import { Text } from "react-native-paper";

import { Screen } from "@/components/Screen";
import { useLocalization } from "@/localization/LocalizationProvider";
import type { Language } from "@/localization/resources";
import { colors } from "@/theme/theme";

const options: { language: Language; labelKey: "settings.english" | "settings.marathi" }[] = [
  { language: "en", labelKey: "settings.english" },
  { language: "mr", labelKey: "settings.marathi" },
];

export function LanguageScreen() {
  const { language, setLanguage, t } = useLocalization();

  return (
    <Screen>
      <Text style={styles.lead} variant="bodyLarge">
        {t("settings.lead")}
      </Text>
      <Text variant="titleMedium">
        {t("settings.current")}: {language === "en" ? t("settings.english") : t("settings.marathi")}
      </Text>
      <View style={styles.options}>
        {options.map((option) => {
          const selected = language === option.language;
          return (
            <Pressable
              accessibilityLabel={t(option.labelKey)}
              accessibilityRole="button"
              accessibilityState={{ selected }}
              key={option.language}
              onPress={() => setLanguage(option.language)}
              style={[styles.option, selected ? styles.selectedOption : null]}
            >
              <Text style={styles.optionLabel} variant="headlineSmall">
                {t(option.labelKey)}
              </Text>
              {selected ? (
                <Text style={styles.selectedText} variant="bodyLarge">
                  {t("diagnose.selected")}
                </Text>
              ) : null}
            </Pressable>
          );
        })}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  lead: {
    fontSize: 18,
    lineHeight: 28,
  },
  options: {
    gap: 12,
  },
  option: {
    backgroundColor: colors.surface,
    borderColor: colors.outline,
    borderRadius: 16,
    borderWidth: 2,
    minHeight: 88,
    justifyContent: "center",
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  selectedOption: {
    backgroundColor: colors.primaryContainer,
    borderColor: colors.primary,
  },
  selectedText: {
    color: colors.primary,
  },
  optionLabel: {
    fontSize: 26,
  },
});
