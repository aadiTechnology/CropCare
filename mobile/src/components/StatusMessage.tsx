import { StyleSheet, View } from "react-native";
import { Text } from "react-native-paper";

import { colors } from "@/theme/theme";

type StatusMessageProps = {
  message: string;
  tone: "empty" | "error" | "info";
};

export function StatusMessage({ message, tone }: StatusMessageProps) {
  return (
    <View accessibilityRole="text" style={[styles.box, styles[tone]]}>
      <Text style={styles.text} variant="bodyLarge">
        {message}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  box: {
    borderRadius: 12,
    borderWidth: 1,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  empty: {
    backgroundColor: colors.surface,
    borderColor: colors.outline,
  },
  error: {
    backgroundColor: "#FDECEA",
    borderColor: colors.error,
  },
  info: {
    backgroundColor: colors.primaryContainer,
    borderColor: colors.primary,
  },
  text: {
    fontSize: 18,
    lineHeight: 26,
  },
});
