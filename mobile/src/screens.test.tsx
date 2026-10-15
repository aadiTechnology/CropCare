import type { ReactElement } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";
import { PaperProvider } from "react-native-paper";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { DiagnoseScreen } from "@/features/diagnosis/DiagnoseScreen";
import { resetDiagnosisSession } from "@/features/diagnosis/diagnosisSession";
import { ResultScreen } from "@/features/diagnosis/ResultScreen";
import { HistoryScreen } from "@/features/history/HistoryScreen";
import { HomeScreen } from "@/features/home/HomeScreen";
import { LocalizationProvider } from "@/localization/LocalizationProvider";
import { LanguageScreen } from "@/features/settings/LanguageScreen";
import { diagnosisService } from "@/services/diagnosis";
import { requestStoredGuidance } from "@/services/guidance/requestGuidance";
import { saveCompletedDiagnosis } from "@/services/history/diagnosisHistory";
import { DiagnosisFailure } from "@/services/inference/DiagnosisFailure";
import { theme } from "@/theme/theme";

const mockPush = jest.fn();
let mockParams: { crop?: string } = {};

jest.mock("expo-router", () => ({
  useRouter: () => ({ push: mockPush }),
  useLocalSearchParams: () => mockParams,
}));

jest.mock("@/services/diagnosis", () => ({
  diagnosisService: {
    analyze: jest.fn(),
  },
}));

jest.mock("@/services/guidance/requestGuidance", () => ({
  requestStoredGuidance: jest.fn(async () => ({ status: "unavailable" })),
}));

jest.mock("@/services/history/diagnosisHistory", () => ({
  saveCompletedDiagnosis: jest.fn(async () => true),
  loadDiagnosisHistory: jest.fn(async () => []),
}));

const mockLaunchImageLibraryAsync = jest.fn();
const mockLaunchCameraAsync = jest.fn();
const mockRequestMediaLibraryPermissionsAsync = jest.fn();
const mockRequestCameraPermissionsAsync = jest.fn();

jest.mock("expo-image-picker", () => ({
  launchImageLibraryAsync: (...args: unknown[]) => mockLaunchImageLibraryAsync(...args),
  launchCameraAsync: (...args: unknown[]) => mockLaunchCameraAsync(...args),
  requestMediaLibraryPermissionsAsync: (...args: unknown[]) =>
    mockRequestMediaLibraryPermissionsAsync(...args),
  requestCameraPermissionsAsync: (...args: unknown[]) => mockRequestCameraPermissionsAsync(...args),
}));

function renderWithProviders(ui: ReactElement) {
  return render(
    <SafeAreaProvider
      initialMetrics={{
        frame: { x: 0, y: 0, width: 390, height: 844 },
        insets: { top: 0, left: 0, right: 0, bottom: 0 },
      }}
    >
      <PaperProvider theme={theme}>
        <LocalizationProvider>{ui}</LocalizationProvider>
      </PaperProvider>
    </SafeAreaProvider>,
  );
}

describe("mobile screens", () => {
  const analyze = diagnosisService.analyze as jest.Mock;
  const requestGuidance = requestStoredGuidance as jest.Mock;
  const saveHistory = saveCompletedDiagnosis as jest.Mock;

  beforeEach(() => {
    mockPush.mockClear();
    analyze.mockReset();
    requestGuidance.mockReset();
    requestGuidance.mockResolvedValue({ status: "unavailable" });
    saveHistory.mockReset();
    saveHistory.mockResolvedValue(true);
    mockParams = {};
    resetDiagnosisSession();
    mockRequestMediaLibraryPermissionsAsync.mockResolvedValue({ granted: true });
    mockRequestCameraPermissionsAsync.mockResolvedValue({ granted: true });
  });

  it("navigates from the home crop cards and primary action", async () => {
    await renderWithProviders(<HomeScreen />);

    expect(screen.getByText("CropCare AI")).toBeTruthy();
    expect(screen.getByText(/farmers in Maharashtra/)).toBeTruthy();
    expect(screen.getByText("Demo data — this is not a real diagnosis")).toBeTruthy();

    await fireEvent.press(screen.getByRole("button", { name: "Soybean" }));
    expect(mockPush).toHaveBeenCalledWith({ pathname: "/diagnose", params: { crop: "soybean" } });

    await fireEvent.press(screen.getByRole("button", { name: "Tomato" }));
    expect(mockPush).toHaveBeenCalledWith({ pathname: "/diagnose", params: { crop: "tomato" } });

    await fireEvent.press(screen.getByRole("button", { name: "Start diagnosis" }));
    expect(mockPush).toHaveBeenCalledWith("/diagnose");

    await fireEvent.press(screen.getByText("View history"));
    expect(mockPush).toHaveBeenCalledWith("/history");
  });

  it("selects a crop and blocks analysis until a photo is chosen", async () => {
    await renderWithProviders(<DiagnoseScreen />);

    expect(
      screen.getByText("No photo selected. Take a photo or choose one from the gallery."),
    ).toBeTruthy();
    expect(screen.getByRole("button", { name: "Soybean" }).props.accessibilityState.selected).toBe(
      true,
    );

    await fireEvent.press(screen.getByRole("button", { name: "Tomato" }));
    expect(screen.getByRole("button", { name: "Tomato" }).props.accessibilityState.selected).toBe(
      true,
    );

    await fireEvent.press(screen.getByText("Analyze image"));
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("shows cancellation and a selected gallery photo", async () => {
    mockLaunchImageLibraryAsync.mockResolvedValueOnce({ canceled: true, assets: null });
    await renderWithProviders(<DiagnoseScreen />);

    await fireEvent.press(screen.getByText("Choose from gallery"));
    expect(await screen.findByText("Photo selection was cancelled.")).toBeTruthy();
    expect(mockPush).not.toHaveBeenCalled();

    mockLaunchImageLibraryAsync.mockResolvedValueOnce({
      canceled: false,
      assets: [{ uri: "file:///leaf.jpg" }],
    });
    await fireEvent.press(screen.getByText("Choose from gallery"));

    expect(await screen.findByLabelText("Selected crop photo")).toBeTruthy();
    expect(screen.getByText("Photo selected.")).toBeTruthy();
  });

  it("shows a permission error when the camera is denied", async () => {
    mockRequestCameraPermissionsAsync.mockResolvedValueOnce({ granted: false });
    await renderWithProviders(<DiagnoseScreen />);

    await fireEvent.press(screen.getByText("Take photo"));

    expect(await screen.findByText("Camera or gallery permission was not granted.")).toBeTruthy();
    expect(mockLaunchCameraAsync).not.toHaveBeenCalled();
  });

  it("shows the tomato class and model confidence after a photo is scored", async () => {
    mockLaunchCameraAsync.mockResolvedValueOnce({
      canceled: false,
      assets: [{ uri: "file:///camera-leaf.jpg" }],
    });
    analyze.mockResolvedValueOnce({
      id: "tomato-test",
      cropType: "tomato",
      predictedDiseaseClass: "tomato_healthy",
      confidence: 0.91,
      modelVersion: "plantvillage_tomato",
      mode: "offline",
      timestamp: "2026-10-14T04:00:00.000Z",
      remedyReference: null,
      isDemo: false,
      status: "model_prediction",
    });
    const diagnose = await renderWithProviders(<DiagnoseScreen />);

    await fireEvent.press(screen.getByRole("button", { name: "Tomato" }));
    await fireEvent.press(screen.getByText("Take photo"));
    expect(await screen.findByText("Photo selected.")).toBeTruthy();

    await fireEvent.press(screen.getByText("Analyze image"));

    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/result"));
    expect(analyze).toHaveBeenCalledWith({
      cropType: "tomato",
      imageUri: "file:///camera-leaf.jpg",
      mode: "offline",
    });
    await diagnose.unmount();

    await renderWithProviders(<ResultScreen />);
    expect(screen.getByText("Healthy")).toBeTruthy();
    expect(screen.getByText("tomato_healthy")).toBeTruthy();
    expect(screen.getByText("91.0% (0.910)")).toBeTruthy();
    expect(screen.getByText("Model confidence")).toBeTruthy();
    expect(
      screen.getByText("This score is the model's own confidence. It is not a guarantee that the class is correct."),
    ).toBeTruthy();
    expect(screen.getByText("plantvillage_tomato")).toBeTruthy();
    expect(screen.getByText("Verified guidance is not available yet.")).toBeTruthy();
    expect(screen.getAllByText("Not available").length).toBe(3);
    expect(screen.queryByText("Demo data — this is not a real diagnosis")).toBeNull();
    expect(requestGuidance).toHaveBeenCalledWith({
      cropCode: "tomato",
      diseaseCode: "tomato_healthy",
    });
    expect(saveHistory).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "tomato-test",
        cropCode: "tomato",
        diseaseClassCode: "tomato_healthy",
        confidence: 0.91,
        modelVersion: "plantvillage_tomato",
        mode: "offline",
      }),
    );
  });

  it("shows a model error and does not open a result when scoring fails", async () => {
    mockLaunchImageLibraryAsync.mockResolvedValueOnce({
      canceled: false,
      assets: [{ uri: "file:///leaf.jpg" }],
    });
    analyze.mockRejectedValueOnce(new DiagnosisFailure("model_unavailable"));
    await renderWithProviders(<DiagnoseScreen initialCrop="tomato" />);

    await fireEvent.press(screen.getByText("Choose from gallery"));
    await fireEvent.press(screen.getByText("Analyze image"));

    expect(await screen.findByText("The tomato model could not be loaded. No class was predicted.")).toBeTruthy();
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("shows the model scoring error when Hermes does not preserve Error subclass identity", async () => {
    mockLaunchImageLibraryAsync.mockResolvedValueOnce({
      canceled: false,
      assets: [{ uri: "file:///leaf.jpg" }],
    });
    analyze.mockRejectedValueOnce(
      Object.assign(new Error("inference_failed"), {
        name: "DiagnosisFailure",
        code: "inference_failed",
      }),
    );
    await renderWithProviders(<DiagnoseScreen initialCrop="tomato" />);

    await fireEvent.press(screen.getByText("Choose from gallery"));
    await fireEvent.press(screen.getByText("Analyze image"));

    expect(await screen.findByText("The model could not score this photo. No class was predicted.")).toBeTruthy();
    expect(screen.queryByText("The photo could not be scored. No class was predicted.")).toBeNull();
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("tells the user that soybean is outside this tomato model", async () => {
    mockLaunchCameraAsync.mockResolvedValueOnce({
      canceled: false,
      assets: [{ uri: "file:///soy.jpg" }],
    });
    analyze.mockRejectedValueOnce(new DiagnosisFailure("unsupported_crop"));
    await renderWithProviders(<DiagnoseScreen />);

    expect(
      screen.getByText("This model only classifies tomato images. Soybean disease detection is not available."),
    ).toBeTruthy();
    await fireEvent.press(screen.getByText("Take photo"));
    await fireEvent.press(screen.getByText("Analyze image"));

    expect(await screen.findByText("This model only classifies tomato images. Soybean disease detection is not available.")).toBeTruthy();
    expect(mockPush).not.toHaveBeenCalled();
    expect(requestGuidance).not.toHaveBeenCalled();
    expect(saveHistory).not.toHaveBeenCalled();
  });

  it("switches the visible language to Marathi", async () => {
    await renderWithProviders(<LanguageScreen />);

    expect(screen.getByText("Choose the app language. English is the default.")).toBeTruthy();
    await fireEvent.press(screen.getByRole("button", { name: "मराठी" }));
    expect(screen.getByText("अॅपची भाषा निवडा. इंग्रजी ही मूळ भाषा आहे.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "मराठी" }).props.accessibilityState.selected).toBe(
      true,
    );
  });

  it("shows saved guidance without copying a missing translation or calling sample text verified", async () => {
    requestGuidance.mockResolvedValueOnce({
      status: "ready",
      content: {
        cropCode: "tomato",
        diseaseCode: "tomato_healthy",
        disease: {
          symptomsEn: "stored-symptom-en",
          symptomsMr: null,
          verificationStatus: "expert_verified",
          source: "test-citation",
          reviewer: "test-reviewer",
          reviewedAt: "2026-10-15T04:30:00Z",
        },
        remedies: [
          {
            remedyEn: null,
            remedyMr: "stored-remedy-mr",
            preventionEn: "stored-prevention-en",
            preventionMr: null,
            verificationStatus: "sample",
            source: null,
            reviewer: null,
            reviewedAt: null,
          },
        ],
      },
    });
    mockLaunchCameraAsync.mockResolvedValueOnce({
      canceled: false,
      assets: [{ uri: "file:///camera-leaf.jpg" }],
    });
    analyze.mockResolvedValueOnce({
      id: "tomato-guidance",
      cropType: "tomato",
      predictedDiseaseClass: "tomato_healthy",
      confidence: 0.91,
      modelVersion: "plantvillage_tomato",
      mode: "offline",
      timestamp: "2026-10-15T04:30:00.000Z",
      remedyReference: null,
      isDemo: false,
      status: "model_prediction",
    });
    const diagnose = await renderWithProviders(<DiagnoseScreen initialCrop="tomato" />);
    await fireEvent.press(screen.getByText("Take photo"));
    await fireEvent.press(screen.getByText("Analyze image"));
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/result"));
    await diagnose.unmount();

    await renderWithProviders(<ResultScreen />);
    expect(screen.getByText("Healthy")).toBeTruthy();
    expect(screen.getByText("stored-symptom-en")).toBeTruthy();
    expect(screen.queryByText("stored-remedy-mr")).toBeNull();
    expect(screen.getByText("stored-prevention-en")).toBeTruthy();
    expect(screen.getByText("Expert verified")).toBeTruthy();
    expect(screen.getByText("Unreviewed")).toBeTruthy();
    expect(screen.getByText("test-citation")).toBeTruthy();
    expect(screen.getByText("test-reviewer")).toBeTruthy();
    expect(screen.getByText("2026-10-15T04:30:00Z")).toBeTruthy();
    expect(screen.getByText("Expert-verified catalog text.")).toBeTruthy();
    expect(screen.getByText("Unreviewed catalog text. This is not expert-verified guidance.")).toBeTruthy();
  });

  it("keeps the prediction visible when guidance and history storage fail", async () => {
    requestGuidance.mockResolvedValueOnce({ status: "unavailable" });
    saveHistory.mockResolvedValueOnce(false);
    mockLaunchImageLibraryAsync.mockResolvedValueOnce({
      canceled: false,
      assets: [{ uri: "file:///leaf.jpg" }],
    });
    analyze.mockResolvedValueOnce({
      id: "tomato-offline",
      cropType: "tomato",
      predictedDiseaseClass: "tomato_early_blight",
      confidence: 0.42,
      modelVersion: "plantvillage_tomato",
      mode: "offline",
      timestamp: "2026-10-15T05:00:00.000Z",
      remedyReference: null,
      isDemo: false,
      status: "model_prediction",
    });
    const diagnose = await renderWithProviders(<DiagnoseScreen initialCrop="tomato" />);
    await fireEvent.press(screen.getByText("Choose from gallery"));
    await fireEvent.press(screen.getByText("Analyze image"));
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/result"));
    expect(saveHistory).toHaveBeenCalled();
    await diagnose.unmount();

    await renderWithProviders(<ResultScreen />);
    expect(screen.getByText("Early blight")).toBeTruthy();
    expect(screen.getByText("42.0% (0.420)")).toBeTruthy();
    expect(screen.getByText("Verified guidance is not available yet.")).toBeTruthy();
  });

  it("shows an empty history state", async () => {
    await renderWithProviders(<HistoryScreen records={[]} />);
    expect(screen.getByText("No records yet.")).toBeTruthy();
    expect(screen.getAllByText("Sample").length).toBe(2);
  });

  it("shows a saved diagnosis apart from the sample records", async () => {
    await renderWithProviders(
      <HistoryScreen
        records={[
          {
            id: "saved-1",
            timestamp: "2026-10-15T04:30:00.000Z",
            cropCode: "tomato",
            diseaseClassCode: "tomato_late_blight",
            confidence: 0.8,
            modelVersion: "plantvillage_tomato",
            mode: "offline",
          },
        ]}
      />,
    );

    expect(screen.getByText("Saved diagnoses")).toBeTruthy();
    expect(screen.getByText("Late blight")).toBeTruthy();
    expect(screen.getByText(/tomato_late_blight/)).toBeTruthy();
    expect(screen.getByText("Sample records")).toBeTruthy();
    expect(screen.getAllByText("Sample").length).toBe(2);
    expect(screen.getAllByText("Sample record").length).toBe(2);
  });
});
