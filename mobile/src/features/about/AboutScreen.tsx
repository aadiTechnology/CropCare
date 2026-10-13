import { StyleSheet, View } from "react-native";
import { Text } from "react-native-paper";

import { Screen } from "@/components/Screen";
import { useLocalization } from "@/localization/LocalizationProvider";
import { colors } from "@/theme/theme";

function Section({ title, body }: { title: string; body: string }) {
  return (
    <View style={styles.section}>
      <Text accessibilityRole="header" style={styles.heading} variant="titleLarge">
        {title}
      </Text>
      <Text variant="bodyLarge">{body}</Text>
    </View>
  );
}

export function AboutScreen() {
  const { t } = useLocalization();

  return (
    <Screen>
      <Text accessibilityRole="header" style={styles.title} variant="headlineSmall">
        {t("appName")}
      </Text>
      <Text variant="bodyLarge">{t("about.description")}</Text>
      <Section body={t("about.cropsBody")} title={t("about.cropsTitle")} />
      <Section body={t("about.stageBody")} title={t("about.stageTitle")} />
      <Section body={t("about.disclaimerBody")} title={t("about.disclaimerTitle")} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: {
    color: colors.primary,
    fontSize: 30,
  },
  section: {
    backgroundColor: colors.surface,
    borderRadius: 14,
    padding: 16,
  },
  heading: {
    marginBottom: 6,
  },
});
