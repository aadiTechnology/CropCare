import {
  createHistoryStore,
  type DiagnosisHistoryStore,
  type HistoryStatus,
  type StoredDiagnosis,
} from "./diagnosisHistoryStore";

export type DiagnosisHistoryView = HistoryStatus & {
  records: StoredDiagnosis[];
};

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
  const view = await loadDiagnosisHistoryView();
  return view.records;
}

export async function loadDiagnosisHistoryView(): Promise<DiagnosisHistoryView> {
  try {
    const store = await openStore();
    const records = await store.load();
    const status = await store.status();
    return { records, ...status };
  } catch {
    return { records: [], unreadableOriginalPresent: false, unreadableCopyPreserved: false };
  }
}
