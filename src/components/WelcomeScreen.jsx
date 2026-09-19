import { Camera, Globe2, Volume2 } from 'lucide-react';

const LANGUAGES = [
  { code: 'bn', label: 'বাংলা' },
  { code: 'te', label: 'తెలుగు' },
];

function WelcomeScreen({ onContinue, language, setLanguage }) {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-sm card p-6 text-center">
        <div className="w-16 h-16 mx-auto rounded-full flex items-center justify-center mb-5" style={{ backgroundColor: 'var(--teal-tint)' }}>
          <span className="text-2xl" style={{ color: 'var(--teal-dark)' }}>📄</span>
        </div>

        <h1 className="text-2xl font-bold leading-snug mb-2">
          Notice, made simple
        </h1>
        <p className="text-sm mb-8" style={{ color: 'var(--ink-soft)' }}>
          Confusing government or landlord notices, explained in your own language — even read aloud.
        </p>

        <div className="space-y-4 text-left mb-8">
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'var(--teal-tint)' }}>
              <Camera size={16} color="var(--teal-dark)" />
            </div>
            <div>
              <p className="font-semibold text-sm">Take a photo</p>
              <p className="text-xs" style={{ color: 'var(--ink-soft)' }}>Of any notice you don't understand</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'var(--amber-tint)' }}>
              <Globe2 size={16} color="var(--amber)" />
            </div>
            <div>
              <p className="font-semibold text-sm">We simplify it</p>
              <p className="text-xs" style={{ color: 'var(--ink-soft)' }}>In plain, everyday language</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'var(--indigo-tint)' }}>
              <Volume2 size={16} color="var(--indigo)" />
            </div>
            <div>
              <p className="font-semibold text-sm">Listen if you prefer</p>
              <p className="text-xs" style={{ color: 'var(--ink-soft)' }}>Hear it read out loud</p>
            </div>
          </div>
        </div>

        <p className="text-xs font-semibold mb-2" style={{ color: 'var(--ink-soft)' }}>Choose your language</p>
        <div className="flex gap-2 justify-center mb-6">
          {LANGUAGES.map((l) => (
            <button
              key={l.code}
              onClick={() => setLanguage(l.code)}
              className="px-5 py-2 rounded-full text-sm font-medium transition"
              style={{
                backgroundColor: language === l.code ? 'var(--teal)' : 'var(--teal-tint)',
                color: language === l.code ? 'white' : 'var(--teal-dark)',
              }}
            >
              {l.label}
            </button>
          ))}
        </div>

        <button
          onClick={onContinue}
          className="w-full py-3 rounded-xl font-semibold text-white transition"
          style={{ backgroundColor: 'var(--teal)' }}
        >
          Get started
        </button>
      </div>
    </div>
  );
}

export default WelcomeScreen;