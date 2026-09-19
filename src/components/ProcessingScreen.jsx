import { useState, useEffect } from 'react';

const RAW_HEADERS = {
  bn: 'কলকাতা পৌরসংস্থা — কর বিভাগ',
  te: 'గ్రేటర్ హైదరాబాద్ మున్సిపల్ కార్పొరేషన్ — పన్ను విభాగం',
};

function ProcessingScreen({ language = 'bn' }) {
  const steps = ["Reading notice", "Simplifying", "Adding audio"];
  const [i, setI] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setI((p) => Math.min(p + 1, steps.length - 1)), 900);
    return () => clearInterval(t);
  }, [steps.length]);

  return (
    <div className="min-h-screen flex items-center justify-center p-5">
      <div className="w-full max-w-sm card p-6 text-center">
        <div className="rounded-xl px-4 py-3 mb-5" style={{ backgroundColor: 'var(--forest-tint)' }}>
          <p className={`font-semibold text-base ${language === 'te' ? 'font-te' : 'font-bn'}`}>{RAW_HEADERS[language] || RAW_HEADERS.bn}</p>
        </div>
        <div className="space-y-2.5 mb-8">
          <div className="h-2.5 rounded-full bg-gray-100 w-full" />
          <div className="h-2.5 rounded-full bg-gray-100 w-3/4" />
          <div className="h-2.5 rounded-full bg-gray-100 w-1/2" />
        </div>
        <p className="text-lg font-bold mb-2">{steps[i]}...</p>
        <p className="text-sm mb-6" style={{ color: 'var(--ink-soft)' }}>This takes a few seconds. Please wait.</p>
        <div className="flex justify-center gap-2.5">
          {steps.map((_, idx) => (
            <span key={idx} className="w-2.5 h-2.5 rounded-full transition-colors" style={{ backgroundColor: idx <= i ? 'var(--rust)' : '#E2E8F0' }} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default ProcessingScreen;