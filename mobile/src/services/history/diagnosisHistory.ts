import { createHistoryStore, type DiagnosisHistoryStore, type StoredDiagnosis } from "./diagnosisHistoryStore";

let storePromise: Promise<DiagnosisHistoryStore> | null = null;

async function openStore(): Promise<DiagnosisHistoryStore> {
  if (!storePromise) {
    storePromise = import("./diagnosisHistoryFile")
      .then((module) => createHistoryStore(module.createDocumentHistoryFile()))
      .catch((error: unknown) => {
        storePromise = null;
        throw error;
      });
  }
  return storePromise;
}

export async function saveCompletedDiagnosis(record: StoredDiagnosis): Promise<boolean> {
  try {
    const store = await openStore();
    return await store.append(record);
  } catch {
    return false;
  }
}

export async function loadDiagnosisHistory(): Promise<StoredDiagnosis[]> {
  try {
    const store = await openStore();
    return await store.load();
  } catch {
    return [];
  }
}
