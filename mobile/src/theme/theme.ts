import { MD3LightTheme, type MD3Theme } from "react-native-paper";

export const colors = {
  primary: "#1B7A3A",
  onPrimary: "#FFFFFF",
  primaryContainer: "#D7F5D8",
  onPrimaryContainer: "#0D3B1A",
  secondary: "#4E5D42",
  background: "#F4F7F2",
  surface: "#FFFFFF",
  surfaceVariant: "#E7EEE4",
  onSurface: "#1C241C",
  onSurfaceVariant: "#3E4A3E",
  outline: "#8A9888",
  error: "#B3261E",
  onError: "#FFFFFF",
  demoBackground: "#FFF6D8",
  demoBorder: "#C8922A",
};

export const theme: MD3Theme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: colors.primary,
    onPrimary: colors.onPrimary,
    primaryContainer: colors.primaryContainer,
    onPrimaryContainer: colors.onPrimaryContainer,
    secondary: colors.secondary,
    background: colors.background,
    surface: colors.surface,
    surfaceVariant: colors.surfaceVariant,
    onSurface: colors.onSurface,
    onSurfaceVariant: colors.onSurfaceVariant,
    outline: colors.outline,
    error: colors.error,
    onError: colors.onError,
  },
};
