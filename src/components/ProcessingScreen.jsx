import { useState, useEffect } from 'react';

function ProcessingScreen() {
  const steps = ["Reading notice", "Simplifying", "Adding audio"];
  const [i, setI] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setI((p) => Math.min(p + 1, steps.length - 1)), 700);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-sm card p-6">
        <div className="rounded-xl px-4 py-3 mb-4" style={{ backgroundColor: 'var(--amber-tint)' }}>
          <p className="font-semibold text-sm font-bn">কলকাতা পৌরসংস্থা — কর বিভাগ</p>
        </div>
        <div className="space-y-2 mb-8">
          <div className="h-2 rounded-full bg-gray-100 w-full" />
          <div className="h-2 rounded-full bg-gray-100 w-3/4" />
          <div className="h-2 rounded-full bg-gray-100 w-1/2" />
        </div>
        <p className="text-center font-semibold mb-3">{steps[i]}...</p>
        <div className="flex justify-center gap-2">
          {steps.map((_, idx) => (
            <span key={idx} className="w-2 h-2 rounded-full transition-colors" style={{ backgroundColor: idx <= i ? 'var(--teal)' : '#E2E8F0' }} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default ProcessingScreen;