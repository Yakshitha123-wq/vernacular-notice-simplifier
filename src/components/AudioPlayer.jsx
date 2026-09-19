import { useState, useRef } from 'react';
import { Play, Pause } from 'lucide-react';

const LANGUAGES = [
  { code: 'bn', label: 'বাংলা' },
  { code: 'te', label: 'తెలుగు' },
];

function AudioPlayer({ audioUrl, language, setLanguage }) {
  const [playing, setPlaying] = useState(false);
  const audioRef = useRef(null);

  const toggle = () => {
    if (!audioRef.current) return;
    playing ? audioRef.current.pause() : audioRef.current.play();
    setPlaying(!playing);
  };

  return (
    <div className="w-full max-w-sm card p-6">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold tracking-wide" style={{ color: 'var(--teal-dark)' }}>SPOKEN AUDIO</p>
        <div className="flex gap-1 bg-gray-100 rounded-full p-1">
          {LANGUAGES.map((l) => (
            <button
              key={l.code}
              onClick={() => setLanguage?.(l.code)}
              aria-label={`Switch audio to ${l.label}`}
              aria-pressed={language === l.code}
              className="text-xs px-2.5 py-1 rounded-full font-medium"
              style={{
                backgroundColor: language === l.code ? 'white' : 'transparent',
                color: language === l.code ? 'var(--teal-dark)' : 'var(--ink-soft)',
                boxShadow: language === l.code ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
              }}
            >
              {l.label}
            </button>
          ))}
        </div>
      </div>

      <p className="text-lg font-bold mb-4">Even read out loud.</p>

      <div className="flex items-center gap-3">
        <button
          onClick={toggle}
          aria-label={playing ? "Pause audio" : "Play audio"}
          className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: 'var(--teal)' }}
        >
          {playing ? <Pause size={16} color="white" fill="white" /> : <Play size={16} color="white" fill="white" />}
        </button>
        <div className="flex-1 h-1.5 rounded-full bg-gray-100 overflow-hidden">
          <div className="h-full bg-gray-300 w-0" />
        </div>
        <span className="text-xs" style={{ color: 'var(--ink-soft)' }}>0:00</span>
      </div>

      {audioUrl && <audio ref={audioRef} src={audioUrl} onEnded={() => setPlaying(false)} className="hidden" />}
    </div>
  );
}

export default AudioPlayer;