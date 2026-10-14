import { DiagnosisFailure } from "./DiagnosisFailure";
import type { ClassLabel } from "./modelContract";

export type ClassPrediction = {
  index: number;
  code: string;
  score: number;
};

const SOFTMAX_SUM_TOLERANCE = 1e-2;

/**
 * Map a softmax vector onto labels.json. Index i is labels[i].code.
 * The score is that class probability, not a guarantee that the class is correct.
 */
export function interpretSoftmax(probabilities: ArrayLike<number>, labels: ClassLabel[]): ClassPrediction {
  if (probabilities.length !== labels.length || labels.length === 0) {
    throw new DiagnosisFailure("inference_failed");
  }

  let bestIndex = 0;
  let bestScore = probabilities[0];
  let sum = 0;
  for (let index = 0; index < probabilities.length; index += 1) {
    const score = probabilities[index];
    if (typeof score !== "number" || !Number.isFinite(score)) {
      throw new DiagnosisFailure("inference_failed");
    }
    sum += score;
    if (score > bestScore) {
      bestScore = score;
      bestIndex = index;
    }
  }

  if (Math.abs(sum - 1) > SOFTMAX_SUM_TOLERANCE) {
    throw new DiagnosisFailure("inference_failed");
  }

  const label = labels[bestIndex];
  if (!label || label.index !== bestIndex) {
    throw new DiagnosisFailure("inference_failed");
  }

  return { index: bestIndex, code: label.code, score: bestScore };
}
