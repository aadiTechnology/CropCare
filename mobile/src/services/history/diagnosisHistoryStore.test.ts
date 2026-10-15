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

function memoryFile(initial: string | null = null): HistoryFileAccess & { text: string | null } {
  const state = { text: initial };
  return {
    get text() {
      return state.text;
    },
    async readText() {
      return state.text;
    },
    async writeText(contents: string) {
      state.text = contents;
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

  it("leaves a corrupt file unchanged when a new save cannot parse it", async () => {
    const file = memoryFile("{not-json");
    const store = createHistoryStore(file);

    await expect(store.append(record)).resolves.toBe(false);
    expect(file.text).toBe("{not-json");
    expect(parseHistoryDocument("{not-json")).toBeNull();
    await expect(store.load()).resolves.toEqual([]);
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
    };

    await expect(createHistoryStore(file).append(record)).resolves.toBe(false);
  });
});
