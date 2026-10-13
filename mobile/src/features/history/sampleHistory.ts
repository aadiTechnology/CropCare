import type { DiagnosisHistoryItem } from "@/types";

/** In-memory sample records. These are not diagnosis results. */
export const SAMPLE_HISTORY: DiagnosisHistoryItem[] = [
  {
    id: "sample-soybean-2026-10-01",
    cropType: "soybean",
    recordedOn: "2026-10-01",
    isDemo: true,
  },
  {
    id: "sample-tomato-2026-09-18",
    cropType: "tomato",
    recordedOn: "2026-09-18",
    isDemo: true,
  },
];
