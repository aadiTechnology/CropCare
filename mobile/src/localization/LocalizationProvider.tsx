import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

import { DEFAULT_LANGUAGE, type Language } from "./resources";
import { translate, type MessageKey } from "./translate";

type LocalizationValue = {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: MessageKey) => string;
};

const LocalizationContext = createContext<LocalizationValue | null>(null);

export function LocalizationProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>(DEFAULT_LANGUAGE);
  const value = useMemo<LocalizationValue>(
    () => ({
      language,
      setLanguage,
      t: (key) => translate(language, key),
    }),
    [language],
  );

  return <LocalizationContext.Provider value={value}>{children}</LocalizationContext.Provider>;
}

export function useLocalization(): LocalizationValue {
  const value = useContext(LocalizationContext);
  if (!value) {
    throw new Error("useLocalization must be used within LocalizationProvider");
  }
  return value;
}
