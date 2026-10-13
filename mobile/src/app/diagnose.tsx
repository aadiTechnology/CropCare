import { useLocalSearchParams } from "expo-router";

import { DiagnoseScreen } from "@/features/diagnosis/DiagnoseScreen";
import { isCropType } from "@/types";

function firstParam(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default function DiagnoseRoute() {
  const params = useLocalSearchParams<{ crop?: string | string[] }>();
  const cropParam = firstParam(params.crop);
  const initialCrop = isCropType(cropParam) ? cropParam : "soybean";

  return <DiagnoseScreen initialCrop={initialCrop} key={initialCrop} />;
}
