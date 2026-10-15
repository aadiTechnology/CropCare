import type { DiagnosisMode } from "@/types";

export type StoredDiagnosis = {
  id: string;
  timestamp: string;
  cropCode: "tomato" | "soybean";
  diseaseClassCode: string;
  confidence: number;
  modelVersion: string;
  mode: DiagnosisMode;
};

export type HistoryFileAccess = {
  readText(): Promise<string | null>;
  writeText(contents: string): Promise<void>;
  preserveUnreadable(contents: string): Promise<void>;
  hasPreservedUnreadable(): Promise<boolean>;
};

export type HistoryStatus = {
  unreadableOriginalPresent: boolean;
  unreadableCopyPreserved: boolean;
};

export type DiagnosisHistoryStore = {
  load(): Promise<StoredDiagnosis[]>;
  status(): Promise<HistoryStatus>;
  append(record: StoredDiagnosis): Promise<boolean>;
};

const DOCUMENT_VERSION = 1;

export function createHistoryStore(file: HistoryFileAccess): DiagnosisHistoryStore {
  let chain: Promise<unknown> = Promise.resolve();

  function exclusive<T>(work: () => Promise<T>): Promise<T> {
    const run = chain.then(work, work);
    chain = run.then(
      () => undefined,
      () => undefined,
    );
    return run;
  }

  return {
    load() {
      return exclusive(async () => {
        try {
          const raw = await file.readText();
          if (raw == null) {
            return [];
          }
          return parseHistoryDocument(raw) ?? [];
        } catch {
          return [];
        }
      });
    },
    status() {
      return exclusive(async () => {
        try {
          const raw = await file.readText();
          return {
            unreadableOriginalPresent: raw != null && parseHistoryDocument(raw) == null,
            unreadableCopyPreserved: await file.hasPreservedUnreadable(),
          };
        } catch {
          return { unreadableOriginalPresent: false, unreadableCopyPreserved: false };
        }
      });
    },
    append(record) {
      if (!isStoredDiagnosis(record)) {
        return Promise.resolve(false);
      }
      return exclusive(async () => {
        try {
          const raw = await file.readText();
          const existing = raw == null ? [] : parseHistoryDocument(raw);
          if (raw != null && existing == null) {
            await file.preserveUnreadable(raw);
            await file.writeText(serializeHistoryDocument([record]));
            return true;
          }
          const records = uniqueKeepingFirst([record, ...(existing ?? [])]);
          await file.writeText(serializeHistoryDocument(records));
          return true;
        } catch {
          return false;
        }
      });
    },
  };
}

export function parseHistoryDocument(raw: string): StoredDiagnosis[] | null {
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object") {
      return null;
    }
    const body = parsed as Record<string, unknown>;
    if (body.version !== DOCUMENT_VERSION || !Array.isArray(body.records)) {
      return null;
    }
    const records = body.records.filter(isStoredDiagnosis);
    return uniqueKeepingFirst(sortNewestFirst(records));
  } catch {
    return null;
  }
}

export function serializeHistoryDocument(records: StoredDiagnosis[]): string {
  return JSON.stringify({ version: DOCUMENT_VERSION, records: sortNewestFirst(records) });
}

function sortNewestFirst(records: StoredDiagnosis[]): StoredDiagnosis[] {
  return [...records].sort((left, right) => {
    if (left.timestamp !== right.timestamp) {
      return left.timestamp < right.timestamp ? 1 : -1;
    }
    if (left.id !== right.id) {
      return left.id < right.id ? 1 : -1;
    }
    return 0;
  });
}

function uniqueKeepingFirst(records: StoredDiagnosis[]): StoredDiagnosis[] {
  const byId = new Map<string, StoredDiagnosis>();
  for (const record of records) {
    if (!byId.has(record.id)) {
      byId.set(record.id, record);
    }
  }
  return sortNewestFirst([...byId.values()]);
}

export function isStoredDiagnosis(value: unknown): value is StoredDiagnosis {
  if (!value || typeof value !== "object") {
    return false;
  }
  const row = value as Record<string, unknown>;
  return (
    typeof row.id === "string" &&
    row.id.trim() !== "" &&
    typeof row.timestamp === "string" &&
    row.timestamp.trim() !== "" &&
    (row.cropCode === "tomato" || row.cropCode === "soybean") &&
    typeof row.diseaseClassCode === "string" &&
    row.diseaseClassCode.trim() !== "" &&
    typeof row.confidence === "number" &&
    Number.isFinite(row.confidence) &&
    typeof row.modelVersion === "string" &&
    row.modelVersion.trim() !== "" &&
    (row.mode === "offline" || row.mode === "online") &&
    !("isDemo" in row)
  );
}
