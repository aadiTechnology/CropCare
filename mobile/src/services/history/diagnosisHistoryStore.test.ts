import { SAMPLE_HISTORY } from "@/features/history/sampleHistory";

import {
  createHistoryStore,
  parseHistoryDocument,
  type HistoryFileAccess,
  type StoredDiagnosis,
} from "./diagnosisHistoryStore";

const record: StoredDiagnosis = {
  id: "tomato-test",
  timestamp: "2026-10-15T04:30:00.000Z",
  cropCode: "tomato",
  diseaseClassCode: "tomato_healthy",
  confidence: 0.91,
  modelVersion: "plantvillage_tomato",
  mode: "offline",
};

function memoryFile(
  initial: string | null = null,
  options?: { preserveError?: boolean },
): HistoryFileAccess & { text: string | null; backups: string[]; writes: number } {
  const state = { text: initial, backups: [] as string[], writes: 0 };
  return {
    get text() {
      return state.text;
    },
    get backups() {
      return state.backups;
    },
    get writes() {
      return state.writes;
    },
    async readText() {
      return state.text;
    },
    async writeText(contents: string) {
      state.writes += 1;
      state.text = contents;
    },
    async preserveUnreadable(contents: string) {
      if (state.text !== contents) {
        throw new Error("active file changed before the backup");
      }
      if (options?.preserveError) {
        throw new Error("backup failed");
      }
      state.backups.push(contents);
    },
    async hasPreservedUnreadable() {
      return state.backups.length > 0;
    },
  };
}

describe("diagnosis history store", () => {
  it("saves a completed prediction and reads it back", async () => {
    const file = memoryFile();
    const store = createHistoryStore(file);

    await expect(store.append(record)).resolves.toBe(true);
    await expect(store.load()).resolves.toEqual([record]);
    await expect(createHistoryStore(memoryFile(file.text)).load()).resolves.toEqual([record]);
  });

  it("does not copy sample records into the saved list", async () => {
    const store = createHistoryStore(memoryFile());
    await store.append(record);
    const saved = await store.load();

    expect(saved).toEqual([record]);
    expect(saved.map((item) => item.id)).not.toEqual(expect.arrayContaining(SAMPLE_HISTORY.map((item) => item.id)));
    expect(SAMPLE_HISTORY.every((item) => item.isDemo)).toBe(true);
  });

  it("keeps a copy of invalid JSON, then saves the new diagnosis and another after it", async () => {
    const original = "{not-json";
    const file = memoryFile(original);
    const store = createHistoryStore(file);
    const later: StoredDiagnosis = {
      ...record,
      id: "later",
      timestamp: "2026-10-16T00:00:00.000Z",
      diseaseClassCode: "tomato_late_blight",
    };

    await expect(store.load()).resolves.toEqual([]);
    expect(file.backups).toEqual([]);
    expect(file.writes).toBe(0);
    await expect(store.status()).resolves.toEqual({
      unreadableOriginalPresent: true,
      unreadableCopyPreserved: false,
    });

    await expect(store.append(record)).resolves.toBe(true);
    expect(file.backups).toEqual([original]);
    expect(parseHistoryDocument(original)).toBeNull();
    await expect(store.load()).resolves.toEqual([record]);
    await expect(store.status()).resolves.toEqual({
      unreadableOriginalPresent: false,
      unreadableCopyPreserved: true,
    });

    await expect(store.append(later)).resolves.toBe(true);
    expect(file.backups).toEqual([original]);
    await expect(store.load()).resolves.toEqual([later, record]);
  });

  it("keeps a copy of a wrong document shape without recreating rows inside it", async () => {
    const original = JSON.stringify({
      version: 2,
      records: [{ id: "lost", diseaseClassCode: "tomato_healthy", confidence: 0.5 }],
    });
    const file = memoryFile(original);
    const store = createHistoryStore(file);

    expect(parseHistoryDocument(original)).toBeNull();
    expect(parseHistoryDocument("[]")).toBeNull();
    await expect(store.append(record)).resolves.toBe(true);
    expect(file.backups).toEqual([original]);
    await expect(store.load()).resolves.toEqual([record]);
    expect(file.text).not.toContain("lost");
  });

  it("leaves the original malformed file unchanged when the backup fails", async () => {
    const original = "{not-json";
    const file = memoryFile(original, { preserveError: true });
    const store = createHistoryStore(file);

    await expect(store.append(record)).resolves.toBe(false);
    expect(file.text).toBe(original);
    expect(file.backups).toEqual([]);
    expect(file.writes).toBe(0);
    await expect(store.load()).resolves.toEqual([]);
    await expect(store.status()).resolves.toEqual({
      unreadableOriginalPresent: true,
      unreadableCopyPreserved: false,
    });
  });

  it("keeps valid records when one row is unreadable and orders newest first", async () => {
    const older: StoredDiagnosis = {
      ...record,
      id: "older",
      timestamp: "2026-10-14T00:00:00.000Z",
      diseaseClassCode: "tomato_early_blight",
    };
    const newer: StoredDiagnosis = {
      ...record,
      id: "newer",
      timestamp: "2026-10-16T00:00:00.000Z",
      diseaseClassCode: "tomato_late_blight",
    };
    const raw = JSON.stringify({
      version: 1,
      records: [older, { id: "broken", confidence: "not-a-number" }, newer, { ...older, timestamp: "2026-10-13T00:00:00.000Z" }],
    });
    const file = memoryFile(raw);
    const store = createHistoryStore(file);

    await expect(store.load()).resolves.toEqual([newer, older]);
    await expect(store.append(record)).resolves.toBe(true);
    await expect(store.load()).resolves.toEqual([newer, record, older]);
    expect(file.text).not.toContain("not-a-number");
    expect(file.backups).toEqual([]);
  });

  it("rejects a sample-shaped record and does not write it", async () => {
    const file = memoryFile();
    const store = createHistoryStore(file);

    await expect(store.append({ ...record, isDemo: true } as StoredDiagnosis)).resolves.toBe(false);
    expect(file.text).toBeNull();
  });

  it("reports a write failure without throwing", async () => {
    const file: HistoryFileAccess = {
      async readText() {
        return null;
      },
      async writeText() {
        throw new Error("disk full");
      },
      async preserveUnreadable() {
        throw new Error("backup failed");
      },
      async hasPreservedUnreadable() {
        return false;
      },
    };

    await expect(createHistoryStore(file).append(record)).resolves.toBe(false);
  });
});
