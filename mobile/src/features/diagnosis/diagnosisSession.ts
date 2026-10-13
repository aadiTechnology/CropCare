import { useSyncExternalStore } from "react";

import type { DiagnosisResult } from "@/types";

export type DiagnosisSession = {
  result: DiagnosisResult;
  imageUri: string;
};

let session: DiagnosisSession | null = null;
const listeners = new Set<() => void>();

function emit(): void {
  listeners.forEach((listener) => listener());
}

export function setDiagnosisSession(next: DiagnosisSession | null): void {
  session = next;
  emit();
}

export function getDiagnosisSession(): DiagnosisSession | null {
  return session;
}

export function resetDiagnosisSession(): void {
  session = null;
  emit();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useDiagnosisSession(): DiagnosisSession | null {
  return useSyncExternalStore(subscribe, getDiagnosisSession, getDiagnosisSession);
}
