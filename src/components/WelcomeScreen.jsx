import { Camera, Globe2, Volume2 } from 'lucide-react';

const LANGUAGES = [
  { code: 'bn', label: 'বাংলা' },
  { code: 'te', label: 'తెలుగు' },
];

function WelcomeScreen({ onContinue, language, setLanguage }) {
  return (
    <div className="min-h-screen flex items-center justify-center p-5">
      <div className="w-full max-w-sm card p-6 text-center">
        <div className="w-20 h-20 mx-auto rounded-full flex items-center justify-center mb-5" style={{ backgroundColor: 'var(--rust-tint)' }}>
          <span className="text-3xl" style={{ color: 'var(--rust-dark)' }}>📄</span>
        </div>

        <h1 className="text-[1.65rem] font-bold leading-snug mb-3">
          Notice, made simple
        </h1>
        <p className="text-base leading-relaxed mb-8" style={{ color: 'var(--ink-soft)' }}>
          Government or landlord notices explained in plain language — and read aloud if you like.
        </p>

        <div className="space-y-4 text-left mb-8">
          <div className="flex items-start gap-4">
            <div className="w-11 h-11 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'var(--rust-tint)' }}>
              <Camera size={20} color="var(--rust-dark)" />
            </div>
            <div>
              <p className="font-semibold text-base">Take a photo or paste text</p>
              <p className="text-sm" style={{ color: 'var(--ink-soft)' }}>Share the notice any way that is easy</p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="w-11 h-11 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'var(--forest-tint)' }}>
              <Globe2 size={20} color="var(--forest)" />
            </div>
            <div>
              <p className="font-semibold text-base">Get a simple summary</p>
              <p className="text-sm" style={{ color: 'var(--ink-soft)' }}>In the language you chose</p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="w-11 h-11 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'var(--indigo-tint)' }}>
              <Volume2 size={20} color="var(--indigo)" />
            </div>
            <div>
              <p className="font-semibold text-base">Tap to listen</p>
              <p className="text-sm" style={{ color: 'var(--ink-soft)' }}>Hear what the notice means</p>
            </div>
          </div>
        </div>

        <p className="text-sm font-semibold mb-3" style={{ color: 'var(--ink-soft)' }}>Pick your language</p>
        <div className="flex gap-3 justify-center mb-7">
          {LANGUAGES.map((l) => (
            <button
              key={l.code}
              onClick={() => setLanguage(l.code)}
              className="px-6 py-3 rounded-full text-base font-semibold transition"
              style={{
                backgroundColor: language === l.code ? 'var(--rust)' : 'var(--rust-tint)',
                color: language === l.code ? 'white' : 'var(--rust-dark)',
              }}
            >
              {l.label}
            </button>
          ))}
        </div>

        <button
          onClick={onContinue}
          className="w-full py-4 rounded-xl font-bold text-lg text-white transition"
          style={{ backgroundColor: 'var(--rust)' }}
        >
          Get started
        </button>
      </div>
    </div>
  );
}

export default WelcomeScreen;