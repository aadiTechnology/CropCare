import "react-native-gesture-handler";

import { PaperProvider } from "react-native-paper";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";

import { LocalizationProvider } from "@/localization/LocalizationProvider";
import { RootNavigator } from "@/navigation/RootNavigator";
import { theme } from "@/theme/theme";

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <PaperProvider theme={theme}>
        <LocalizationProvider>
          <RootNavigator />
          <StatusBar style="light" />
        </LocalizationProvider>
      </PaperProvider>
    </SafeAreaProvider>
  );
}
