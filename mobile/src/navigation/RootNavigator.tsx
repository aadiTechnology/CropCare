import { Stack } from "expo-router";

import { useLocalization } from "@/localization/LocalizationProvider";
import { colors } from "@/theme/theme";

export function RootNavigator() {
  const { t } = useLocalization();

  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: colors.primary },
        headerTintColor: colors.onPrimary,
        headerTitleStyle: { fontSize: 20 },
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      <Stack.Screen name="index" options={{ title: t("nav.home") }} />
      <Stack.Screen name="diagnose" options={{ title: t("nav.diagnose") }} />
      <Stack.Screen name="result" options={{ title: t("nav.result") }} />
      <Stack.Screen name="history" options={{ title: t("nav.history") }} />
      <Stack.Screen name="about" options={{ title: t("nav.about") }} />
      <Stack.Screen name="settings/language" options={{ title: t("nav.language") }} />
    </Stack>
  );
}
