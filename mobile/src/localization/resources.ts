export type Language = "en" | "mr";

export const DEFAULT_LANGUAGE: Language = "en";

export type Messages = {
  appName: string;
  common: {
    demoBanner: string;
    sample: string;
    loading: string;
    error: string;
    unavailable: string;
  };
  nav: {
    home: string;
    diagnose: string;
    result: string;
    history: string;
    language: string;
    about: string;
  };
  home: {
    welcome: string;
    startDiagnosis: string;
    recent: string;
    sampleNote: string;
    openHistory: string;
    openLanguage: string;
    openAbout: string;
  };
  crops: {
    soybean: string;
    tomato: string;
  };
  diagnose: {
    selectCrop: string;
    selected: string;
    previewPlaceholder: string;
    imagePreview: string;
    imageSelected: string;
    takePhoto: string;
    chooseGallery: string;
    analyze: string;
    analyzeHint: string;
    noImage: string;
    cancelled: string;
    permissionDenied: string;
    analyzeError: string;
  };
  result: {
    crop: string;
    disease: string;
    confidence: string;
    symptoms: string;
    remedy: string;
    prevention: string;
    disclaimer: string;
    mode: string;
    modelVersion: string;
    time: string;
    offlineInactive: string;
    onlineInactive: string;
    placeholderBody: string;
    empty: string;
    emptyAction: string;
  };
  history: {
    empty: string;
    sampleLabel: string;
    date: string;
  };
  settings: {
    lead: string;
    english: string;
    marathi: string;
    current: string;
  };
  about: {
    description: string;
    cropsTitle: string;
    cropsBody: string;
    stageTitle: string;
    stageBody: string;
    disclaimerTitle: string;
    disclaimerBody: string;
  };
};

export const resources: Record<Language, Messages> = {
  en: {
    appName: "CropCare AI",
    common: {
      demoBanner: "Demo data — this is not a real diagnosis",
      sample: "Sample",
      loading: "Please wait…",
      error: "Something went wrong. Please try again.",
      unavailable: "Not available",
    },
    nav: {
      home: "Home",
      diagnose: "Diagnose",
      result: "Result preview",
      history: "History",
      language: "Language",
      about: "About",
    },
    home: {
      welcome:
        "Welcome. This academic app helps farmers in Maharashtra inspect soybean and tomato plants.",
      startDiagnosis: "Start diagnosis",
      recent: "Recent diagnoses",
      sampleNote: "The records below are samples. They are not real diagnoses.",
      openHistory: "View history",
      openLanguage: "Language settings",
      openAbout: "About this app",
    },
    crops: {
      soybean: "Soybean",
      tomato: "Tomato",
    },
    diagnose: {
      selectCrop: "Choose a crop",
      selected: "Selected",
      previewPlaceholder: "The photo will appear here",
      imagePreview: "Selected crop photo",
      imageSelected: "Photo selected.",
      takePhoto: "Take photo",
      chooseGallery: "Choose from gallery",
      analyze: "Analyze image",
      analyzeHint: "This version shows a development preview. It does not detect a disease.",
      noImage: "No photo selected. Take a photo or choose one from the gallery.",
      cancelled: "Photo selection was cancelled.",
      permissionDenied: "Camera or gallery permission was not granted.",
      analyzeError: "The preview could not be opened.",
    },
    result: {
      crop: "Crop",
      disease: "Disease label",
      confidence: "Confidence",
      symptoms: "Symptoms",
      remedy: "Remedy",
      prevention: "Prevention",
      disclaimer:
        "This is a development preview. It is not a diagnosis. A trained model and expert-verified guidance are not connected yet.",
      mode: "Diagnosis mode",
      modelVersion: "Model version",
      time: "Time",
      offlineInactive: "On this phone — model not connected",
      onlineInactive: "Online service — model not connected",
      placeholderBody: "Expert-verified text is not available in this version.",
      empty: "There is no preview yet. Choose a photo and analyze it first.",
      emptyAction: "Go to diagnosis",
    },
    history: {
      empty: "No records yet.",
      sampleLabel: "Sample record",
      date: "Date",
    },
    settings: {
      lead: "Choose the app language. English is the default.",
      english: "English",
      marathi: "मराठी",
      current: "Current language",
    },
    about: {
      description:
        "CropCare AI is an academic app for soybean and tomato disease detection, being built for farmers in Maharashtra.",
      cropsTitle: "Supported crops",
      cropsBody: "Soybean and tomato.",
      stageTitle: "Development stage",
      stageBody:
        "Sprint 1 sets up the mobile app and the server. Disease detection is not available yet.",
      disclaimerTitle: "Academic use",
      disclaimerBody:
        "This app is for academic use. Sample text is not expert-verified farming advice.",
    },
  },
  mr: {
    appName: "क्रॉपकेअर एआय",
    common: {
      demoBanner: "नमुना डेटा — हे प्रत्यक्ष निदान नाही",
      sample: "नमुना",
      loading: "कृपया थांबा…",
      error: "काहीतरी चुकले. पुन्हा प्रयत्न करा.",
      unavailable: "उपलब्ध नाही",
    },
    nav: {
      home: "मुख्यपृष्ठ",
      diagnose: "निदान",
      result: "निकालाचा नमुना",
      history: "इतिहास",
      language: "भाषा",
      about: "माहिती",
    },
    home: {
      welcome:
        "स्वागत आहे. हे शैक्षणिक अॅप महाराष्ट्रातील शेतकऱ्यांना सोयाबीन आणि टोमॅटो तपासण्यास मदत करते.",
      startDiagnosis: "निदान सुरू करा",
      recent: "अलीकडील निदान",
      sampleNote: "खालील नोंदी नमुना आहेत. त्या प्रत्यक्ष निदान नाहीत.",
      openHistory: "इतिहास पाहा",
      openLanguage: "भाषा सेटिंग्ज",
      openAbout: "अॅपबद्दल",
    },
    crops: {
      soybean: "सोयाबीन",
      tomato: "टोमॅटो",
    },
    diagnose: {
      selectCrop: "पीक निवडा",
      selected: "निवडले",
      previewPlaceholder: "फोटो येथे दिसेल",
      imagePreview: "निवडलेल्या पिकाचा फोटो",
      imageSelected: "फोटो निवडला आहे.",
      takePhoto: "फोटो काढा",
      chooseGallery: "गॅलरीमधून निवडा",
      analyze: "प्रतिमेचे विश्लेषण करा",
      analyzeHint: "ही आवृत्ती फक्त विकास नमुना दाखवते. ती रोग ओळखत नाही.",
      noImage: "फोटो निवडलेला नाही. फोटो काढा किंवा गॅलरीमधून निवडा.",
      cancelled: "फोटो निवड रद्द झाली.",
      permissionDenied: "कॅमेरा किंवा गॅलरीची परवानगी मिळाली नाही.",
      analyzeError: "नमुना उघडता आला नाही.",
    },
    result: {
      crop: "पीक",
      disease: "रोगाचे नाव",
      confidence: "खात्रीची पातळी",
      symptoms: "लक्षणे",
      remedy: "उपाय",
      prevention: "प्रतिबंध",
      disclaimer:
        "हा विकास टप्प्यातील नमुना आहे. हे निदान नाही. प्रशिक्षित मॉडेल आणि तज्ञांनी पडताळलेले मार्गदर्शन अद्याप जोडलेले नाही.",
      mode: "निदान पद्धत",
      modelVersion: "मॉडेल आवृत्ती",
      time: "वेळ",
      offlineInactive: "या फोनवर — मॉडेल जोडलेले नाही",
      onlineInactive: "ऑनलाइन सेवा — मॉडेल जोडलेले नाही",
      placeholderBody: "या आवृत्तीत तज्ञांनी पडताळलेला मजकूर उपलब्ध नाही.",
      empty: "अद्याप नमुना नाही. आधी फोटो निवडून विश्लेषण करा.",
      emptyAction: "निदानाकडे जा",
    },
    history: {
      empty: "अद्याप कोणतीही नोंद नाही.",
      sampleLabel: "नमुना नोंद",
      date: "दिनांक",
    },
    settings: {
      lead: "अॅपची भाषा निवडा. इंग्रजी ही मूळ भाषा आहे.",
      english: "English",
      marathi: "मराठी",
      current: "सध्याची भाषा",
    },
    about: {
      description:
        "क्रॉपकेअर एआय हे सोयाबीन आणि टोमॅटोच्या रोग ओळखीसाठी तयार होत असलेले शैक्षणिक अॅप आहे. हे महाराष्ट्रातील शेतकऱ्यांसाठी आहे.",
      cropsTitle: "समर्थित पिके",
      cropsBody: "सोयाबीन आणि टोमॅटो.",
      stageTitle: "विकास टप्पा",
      stageBody: "स्प्रिंट १ मध्ये अॅप आणि सर्व्हरची सुरुवात आहे. रोग ओळख अद्याप उपलब्ध नाही.",
      disclaimerTitle: "शैक्षणिक वापर",
      disclaimerBody: "हे अॅप शैक्षणिक वापरासाठी आहे. नमुना मजकूर तज्ञांनी पडताळलेला शेती सल्ला नाही.",
    },
  },
};

export function collectMessageKeys(node: object, prefix = ""): string[] {
  return Object.entries(node).flatMap(([key, value]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    if (value !== null && typeof value === "object") {
      return collectMessageKeys(value, path);
    }
    return [path];
  });
}
