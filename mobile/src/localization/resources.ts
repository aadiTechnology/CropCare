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
    tomatoOnly: string;
    modelUnavailable: string;
    imageUnreadable: string;
    inferenceFailed: string;
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
    predictedClass: string;
    classCode: string;
    confidenceNote: string;
    modelDisclaimer: string;
    offlineOnDevice: string;
    guidanceUnavailable: string;
    guidanceSample: string;
    guidanceVerified: string;
    verificationStatus: string;
    statusSample: string;
    statusExpert: string;
    source: string;
    reviewer: string;
    reviewedAt: string;
  };
  classes: {
    tomato_bacterial_spot: string;
    tomato_early_blight: string;
    tomato_healthy: string;
    tomato_late_blight: string;
    tomato_leaf_mold: string;
    tomato_mosaic_virus: string;
    tomato_septoria_leaf_spot: string;
    tomato_spider_mites: string;
    tomato_target_spot: string;
    tomato_yellow_leaf_curl_virus: string;
  };
  history: {
    empty: string;
    sampleLabel: string;
    date: string;
    savedHeading: string;
    sampleHeading: string;
    confidence: string;
    modelVersion: string;
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
      analyzeHint:
        "Choose tomato to score a leaf photo on this phone. The score is the model's confidence, not a confirmed diagnosis. This model does not cover soybean.",
      noImage: "No photo selected. Take a photo or choose one from the gallery.",
      cancelled: "Photo selection was cancelled.",
      permissionDenied: "Camera or gallery permission was not granted.",
      analyzeError: "The photo could not be scored. No class was predicted.",
      tomatoOnly: "This model only classifies tomato images. Soybean disease detection is not available.",
      modelUnavailable: "The tomato model could not be loaded. No class was predicted.",
      imageUnreadable: "This photo could not be read as pixels. No class was predicted.",
      inferenceFailed: "The model could not score this photo. No class was predicted.",
    },
    result: {
      crop: "Crop",
      disease: "Disease label",
      confidence: "Model confidence",
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
      empty: "There is no result yet. Choose a tomato photo and analyze it first.",
      emptyAction: "Go to diagnosis",
      predictedClass: "Predicted class",
      classCode: "Class code",
      confidenceNote:
        "This score is the model's own confidence. It is not a guarantee that the class is correct.",
      modelDisclaimer:
        "This is the on-device tomato model's class and confidence. It is not a confirmed diagnosis.",
      offlineOnDevice: "On this phone",
      guidanceUnavailable: "Verified guidance is not available yet.",
      guidanceSample: "Unreviewed catalog text. This is not expert-verified guidance.",
      guidanceVerified: "Expert-verified catalog text.",
      verificationStatus: "Verification status",
      statusSample: "Unreviewed",
      statusExpert: "Expert verified",
      source: "Source",
      reviewer: "Reviewer",
      reviewedAt: "Review date",
    },
    classes: {
      tomato_bacterial_spot: "Bacterial spot",
      tomato_early_blight: "Early blight",
      tomato_healthy: "Healthy",
      tomato_late_blight: "Late blight",
      tomato_leaf_mold: "Leaf mold",
      tomato_mosaic_virus: "Mosaic virus",
      tomato_septoria_leaf_spot: "Septoria leaf spot",
      tomato_spider_mites: "Spider mites",
      tomato_target_spot: "Target spot",
      tomato_yellow_leaf_curl_virus: "Yellow leaf curl virus",
    },
    history: {
      empty: "No records yet.",
      sampleLabel: "Sample record",
      date: "Date",
      savedHeading: "Saved diagnoses",
      sampleHeading: "Sample records",
      confidence: "Model confidence",
      modelVersion: "Model version",
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
      cropsBody: "Tomato leaf photos can be scored on this phone. Soybean disease detection is not available.",
      stageTitle: "Development stage",
      stageBody:
        "The PlantVillage tomato model scores a tomato photo on this phone. That score is model confidence, not a confirmed diagnosis. Soybean disease detection and expert remedies are not available.",
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
      analyzeHint:
        "पानाचा फोटो या फोनवर तपासण्यासाठी टोमॅटो निवडा. गुण म्हणजे मॉडेलची खात्री आहे, खात्रीशीर निदान नाही. हे मॉडेल सोयाबीनला लागू होत नाही.",
      noImage: "फोटो निवडलेला नाही. फोटो काढा किंवा गॅलरीमधून निवडा.",
      cancelled: "फोटो निवड रद्द झाली.",
      permissionDenied: "कॅमेरा किंवा गॅलरीची परवानगी मिळाली नाही.",
      analyzeError: "फोटो तपासता आला नाही. कोणताही वर्ग अंदाजित केला नाही.",
      tomatoOnly: "हे मॉडेल फक्त टोमॅटोच्या प्रतिमा वर्गीकृत करते. सोयाबीनच्या रोगाची ओळख उपलब्ध नाही.",
      modelUnavailable: "टोमॅटो मॉडेल लोड होऊ शकले नाही. कोणताही वर्ग अंदाजित केला नाही.",
      imageUnreadable: "हा फोटो पिक्सेल म्हणून वाचता आला नाही. कोणताही वर्ग अंदाजित केला नाही.",
      inferenceFailed: "मॉडेलला या फोटोचे गुण देता आले नाहीत. कोणताही वर्ग अंदाजित केला नाही.",
    },
    result: {
      crop: "पीक",
      disease: "रोगाचे नाव",
      confidence: "मॉडेलची खात्री",
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
      empty: "अद्याप निकाल नाही. आधी टोमॅटोचा फोटो निवडून विश्लेषण करा.",
      emptyAction: "निदानाकडे जा",
      predictedClass: "अंदाजित वर्ग",
      classCode: "वर्ग संकेत",
      confidenceNote: "हा गुण मॉडेलची स्वतःची खात्री आहे. वर्ग बरोबर आहे याची हमी नाही.",
      modelDisclaimer:
        "हा या फोनवरील टोमॅटो मॉडेलचा वर्ग आणि खात्रीचा गुण आहे. हे खात्रीशीर निदान नाही.",
      offlineOnDevice: "या फोनवर",
      guidanceUnavailable: "पडताळलेले मार्गदर्शन अद्याप उपलब्ध नाही.",
      guidanceSample: "हा पडताळणी न झालेला सूची मजकूर आहे. हे तज्ञांनी पडताळलेले मार्गदर्शन नाही.",
      guidanceVerified: "हा तज्ञांनी पडताळलेला सूची मजकूर आहे.",
      verificationStatus: "पडताळणी स्थिती",
      statusSample: "पडताळणी बाकी",
      statusExpert: "तज्ञांनी पडताळलेले",
      source: "स्रोत",
      reviewer: "पडताळणी करणारे",
      reviewedAt: "पडताळणीची तारीख",
    },
    classes: {
      tomato_bacterial_spot: "बॅक्टेरियल स्पॉट",
      tomato_early_blight: "अर्ली ब्लाइट",
      tomato_healthy: "निरोगी",
      tomato_late_blight: "लेट ब्लाइट",
      tomato_leaf_mold: "लीफ मोल्ड",
      tomato_mosaic_virus: "मोझेक विषाणू",
      tomato_septoria_leaf_spot: "सेप्टोरिया लीफ स्पॉट",
      tomato_spider_mites: "स्पायडर माइट्स",
      tomato_target_spot: "टार्गेट स्पॉट",
      tomato_yellow_leaf_curl_virus: "यलो लीफ कर्ल विषाणू",
    },
    history: {
      empty: "अद्याप कोणतीही नोंद नाही.",
      sampleLabel: "नमुना नोंद",
      date: "दिनांक",
      savedHeading: "जतन केलेली निदाने",
      sampleHeading: "नमुना नोंदी",
      confidence: "मॉडेलची खात्री",
      modelVersion: "मॉडेल आवृत्ती",
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
      cropsBody: "टोमॅटोच्या पानाचे फोटो या फोनवर तपासता येतात. सोयाबीनच्या रोगाची ओळख उपलब्ध नाही.",
      stageTitle: "विकास टप्पा",
      stageBody:
        "प्लांटव्हिलेज टोमॅटो मॉडेल टोमॅटोचा फोटो या फोनवर तपासते. गुण म्हणजे मॉडेलची खात्री आहे, खात्रीशीर निदान नाही. सोयाबीनच्या रोगाची ओळख आणि तज्ञांचे उपाय उपलब्ध नाहीत.",
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
