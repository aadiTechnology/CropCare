import { File, Paths } from "expo-file-system";

import type { HistoryFileAccess } from "./diagnosisHistoryStore";

const HISTORY_FILE_NAME = "cropcare-diagnosis-history.json";

export function createDocumentHistoryFile(): HistoryFileAccess {
  const file = new File(Paths.document, HISTORY_FILE_NAME);
  return {
    async readText() {
      if (!file.exists) {
        return null;
      }
      return file.text();
    },
    async writeText(contents: string) {
      if (!file.exists) {
        file.create({ intermediates: true });
      }
      file.write(contents);
    },
  };
}
