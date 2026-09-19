import { useState } from 'react';
import WelcomeScreen from './components/WelcomeScreen';
import UploadScreen from './components/UploadScreen';
import ProcessingScreen from './components/ProcessingScreen';
import ResultScreen from './components/ResultScreen';
import { getUploadUrl, uploadToS3, processNotice, processText } from './lib/api';

const USE_MOCK = false;

function App() {
  const [screen, setScreen] = useState('welcome');
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [language, setLanguage] = useState('te');
  const [error, setError] = useState(null);

  const startProcessing = () => {
    setError(null);
    setProgress(0);
    setScreen('processing');
  };

  const handleUpload = async (file) => {
    setError(null);
    setScreen('uploading');
    setProgress(0);

    if (USE_MOCK) {
      let p = 0;
      const t = setInterval(() => {
        p += 20;
        setProgress(p);
        if (p >= 100) {
          clearInterval(t);
          startProcessing();
          setTimeout(() => {
            setResult({ category: "Tax/Fine", simplified_summary: "Pay your property tax before 30 September.", actionable_steps: ["Pay online or at the ward office"], deadlines: ["2026-09-30"], target_audience: "Property owners", original_text: file.type, audio_url: null });
            setScreen('result');
          }, 2200);
        }
      }, 150);
      return;
    }

    try {
      const { uploadUrl, fileKey } = await getUploadUrl(file.type);
      await uploadToS3(uploadUrl, file, setProgress);
      startProcessing();
      const data = await processNotice(fileKey, language);
      setResult(data);
      setScreen('result');
    } catch (err) {
      console.error(err);
      setError(err.message || 'Something went wrong. Please try again.');
      setScreen('upload');
    }
  };

  const handleTextSubmit = async (text) => {
    setError(null);
    startProcessing();
    try {
      const data = await processText(text, language);
      setResult(data);
      setScreen('result');
    } catch (err) {
      console.error(err);
      setError(err.message || "We couldn't simplify that notice. Please try again.");
      setScreen('upload');
    }
  };

  const handleReset = () => {
    setScreen('upload');
    setResult(null);
    setProgress(0);
    setError(null);
  };

  return (
    <>
      {screen === 'welcome' && <WelcomeScreen onContinue={() => setScreen('upload')} language={language} setLanguage={setLanguage} />}
      {screen === 'upload' && <UploadScreen onUpload={handleUpload} onTextSubmit={handleTextSubmit} error={error} language={language} setLanguage={setLanguage} />}
      {screen === 'uploading' && <UploadScreen uploading progress={progress} />}
      {screen === 'processing' && <ProcessingScreen language={language} />}
      {screen === 'result' && <ResultScreen data={result} onReset={handleReset} language={language} setLanguage={setLanguage} />}
    </>
  );
}

export default App;