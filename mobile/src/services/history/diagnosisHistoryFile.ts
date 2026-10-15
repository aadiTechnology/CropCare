import { File, Paths } from "expo-file-system";

import type { HistoryFileAccess } from "./diagnosisHistoryStore";

const HISTORY_FILE_NAME = "cropcare-diagnosis-history.json";
const UNREADABLE_BACKUP_PREFIX = "cropcare-diagnosis-history.unreadable-";

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
    async preserveUnreadable(contents: string) {
      const backup = new File(Paths.document, `${UNREADABLE_BACKUP_PREFIX}${Date.now()}.json`);
      if (backup.exists) {
        throw new Error("history backup already exists");
      }
      backup.create({ intermediates: true });
      try {
        backup.write(contents);
        const stored = await backup.text();
        if (stored !== contents) {
          throw new Error("history backup did not match the original");
        }
      } catch (error) {
        if (backup.exists) {
          backup.delete();
        }
        throw error;
      }
    },
    async hasPreservedUnreadable() {
      try {
        return Paths.document
          .list()
          .some((entry) => entry instanceof File && entry.name.startsWith(UNREADABLE_BACKUP_PREFIX));
      } catch {
        return false;
      }
    },
  };
}
