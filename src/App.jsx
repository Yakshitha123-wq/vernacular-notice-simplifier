import { useState } from 'react';
import WelcomeScreen from './components/WelcomeScreen';
import UploadScreen from './components/UploadScreen';
import ProcessingScreen from './components/ProcessingScreen';
import ResultScreen from './components/ResultScreen';
import { getUploadUrl, uploadToS3, processNotice } from './lib/api';

const USE_MOCK = true;

const MOCK_RESULTS = {
  bn: {
    category: "Public Health Advisory",
    original_text: "অধ্যাদেশ অনুযায়ী সমাবেশ নিষিদ্ধ। কলকাতা পৌরসংস্থা কর বিভাগ কর্তৃক জারিকৃত এই বিজ্ঞপ্তি অনুযায়ী...",
    simplified_summary: "আপনার বাড়ির কর আগামী ৩০ সেপ্টেম্বরের মধ্যে দিন। দেরি করলে প্রতি মাসে ১০% বেশি দিতে হবে।",
    actionable_steps: ["অনলাইনে বা ওয়ার্ড অফিসে পরিশোধ করুন", "রসিদটা রেখে দিন"],
    deadlines: ["30 September 2026"],
    target_audience: "Property owners",
    audio_url: null,
  },
  te: {
    category: "Public Health Advisory",
    original_text: "ఆదేశాల ప్రకారం నలుగురు కంటే ఎక్కువ మంది గుమిగూడటం నిషేధించబడింది. గ్రేటర్ హైదరాబాద్ మున్సిపల్ కార్పొరేషన్ జారీ చేసిన ఈ నోటీసు ప్రకారం...",
    simplified_summary: "మీ ఇంటి పన్ను సెప్టెంబర్ 30లోపు కట్టండి. ఆలస్యం చేస్తే ప్రతి నెలా 10% ఎక్కువ కట్టాలి.",
    actionable_steps: ["ఆన్‌లైన్‌లో లేదా వార్డు కార్యాలయంలో చెల్లించండి", "రసీదు దగ్గర ఉంచుకోండి"],
    deadlines: ["30 September 2026"],
    target_audience: "Property owners",
    audio_url: null,
  },
};

function App() {
  const [screen, setScreen] = useState('welcome');
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [language, setLanguage] = useState('te');

  const handleUpload = async (file) => {
    setScreen('uploading');
    setProgress(0);

    if (USE_MOCK) {
      let p = 0;
      const t = setInterval(() => {
        p += 20;
        setProgress(p);
        if (p >= 100) {
          clearInterval(t);
          setScreen('processing');
          setTimeout(() => {
            setResult(MOCK_RESULTS[language]);
            setScreen('result');
          }, 2200);
        }
      }, 150);
      return;
    }

    try {
      const { uploadUrl, fileKey } = await getUploadUrl(file.type);
      await uploadToS3(uploadUrl, file, setProgress);
      setScreen('processing');
      const data = await processNotice(fileKey, language);
      setResult(data);
      setScreen('result');
    } catch (err) {
      console.error(err);
      setScreen('upload');
    }
  };

  const handleReset = () => {
    setScreen('upload');
    setResult(null);
    setProgress(0);
  };

  return (
    <>
      {screen === 'welcome' && <WelcomeScreen onContinue={() => setScreen('upload')} language={language} setLanguage={setLanguage} />}
      {screen === 'upload' && <UploadScreen onUpload={handleUpload} language={language} setLanguage={setLanguage} />}
      {screen === 'uploading' && <UploadScreen uploading progress={progress} />}
      {screen === 'processing' && <ProcessingScreen />}
      {screen === 'result' && <ResultScreen data={result} onReset={handleReset} language={language} setLanguage={setLanguage} />}
    </>
  );
}

export default App;