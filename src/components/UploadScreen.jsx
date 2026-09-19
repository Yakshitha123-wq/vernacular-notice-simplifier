import { useState } from 'react';
import { Camera, FileText } from 'lucide-react';

const LANGUAGES = [
  { code: 'bn', label: 'বাংলা' },
  { code: 'te', label: 'తెలుగు' },
];

function UploadScreen({ onUpload, onTextSubmit, error, language, setLanguage, uploading, progress }) {
  const [isDragging, setIsDragging] = useState(false);
  const [mode, setMode] = useState(language === 'bn' || language === 'te' ? 'text' : 'photo');
  const [text, setText] = useState('');

  const handleFile = (file) => file && onUpload(file);
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-5">
      <div className="w-full max-w-sm card p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: 'var(--rust)' }} />
            <span className="font-semibold text-base">Notice, made simple</span>
          </div>
          {!uploading && (
            <div className="flex gap-1 bg-gray-100 rounded-full p-1">
              {LANGUAGES.map((l) => (
                <button
                  key={l.code}
                  onClick={() => setLanguage(l.code)}
                  aria-label={`Switch language to ${l.label}`}
                  aria-pressed={language === l.code}
                  className="text-sm px-3 py-1.5 rounded-full font-semibold transition"
                  style={{
                    backgroundColor: language === l.code ? 'white' : 'transparent',
                    color: language === l.code ? 'var(--rust-dark)' : 'var(--ink-soft)',
                    boxShadow: language === l.code ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                  }}
                >
                  {l.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {uploading ? (
          <div className="py-10">
            <p className="text-center text-lg font-bold mb-4">Uploading your notice...</p>
            <div className="h-3 rounded-full bg-gray-100 overflow-hidden">
              <div className="h-full rounded-full transition-all" style={{ width: `${progress}%`, backgroundColor: 'var(--rust)' }} />
            </div>
            <p className="text-center text-sm mt-3" style={{ color: 'var(--ink-soft)' }}>{progress}%</p>
          </div>
        ) : (
          <>
            <h1 className="text-[1.4rem] font-bold leading-snug mb-3">
              Share the notice you want to understand
            </h1>
            <p className="text-base leading-relaxed mb-6" style={{ color: 'var(--ink-soft)' }}>
              We will explain it simply in {LANGUAGES.find(l => l.code === language)?.label}.
            </p>

            <div className="flex gap-1 bg-gray-100 rounded-full p-1 mb-5" role="tablist" aria-label="How to share your notice">
              {[['photo', 'Photo'], ['text', 'Paste text']].map(([key, label]) => (
                <button
                  key={key}
                  role="tab"
                  aria-selected={mode === key}
                  onClick={() => setMode(key)}
                  className="flex-1 text-sm px-2.5 py-2 rounded-full font-semibold transition"
                  style={{
                    backgroundColor: mode === key ? 'white' : 'transparent',
                    color: mode === key ? 'var(--rust-dark)' : 'var(--ink-soft)',
                    boxShadow: mode === key ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                  }}
                >
                  {label}
                </button>
              ))}
            </div>

            {(language === 'bn' || language === 'te') && mode === 'photo' && (
              <p className="text-sm mb-4 px-4 py-3 rounded-xl" style={{ backgroundColor: 'var(--rust-tint)', color: 'var(--rust-dark)' }}>
                For Bengali or Telugu notices, please paste the text. The photo reader works best for English notices right now.
              </p>
            )}

            {mode === 'photo' ? (
              <label
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                aria-label="Take or upload a photo of the notice"
                className="block border-2 border-dashed rounded-2xl py-12 text-center cursor-pointer transition"
                style={{ borderColor: isDragging ? 'var(--rust)' : '#CFE8E0', backgroundColor: isDragging ? 'var(--rust-tint)' : 'transparent' }}
              >
                <input type="file" accept="image/*" capture="environment" onChange={(e) => handleFile(e.target.files[0])} className="hidden" />
                <div className="w-16 h-16 mx-auto rounded-full flex items-center justify-center mb-4" style={{ backgroundColor: 'var(--rust-tint)' }}>
                  <Camera size={28} color="var(--rust-dark)" />
                </div>
                <p className="font-bold text-base">Tap to take or upload a photo</p>
                <p className="text-sm mt-1" style={{ color: 'var(--ink-soft)' }}>JPG, PNG or WEBP — or drag it here</p>
              </label>
            ) : (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <FileText size={18} color="var(--rust-dark)" />
                  <span className="text-sm font-semibold" style={{ color: 'var(--rust-dark)' }}>Paste the notice text</span>
                </div>
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  rows={7}
                  placeholder="Copy the notice text and paste it here..."
                  aria-label="Paste the notice text"
                  className="w-full resize-none rounded-xl border px-4 py-3 text-base focus:outline-none focus:ring-2"
                  style={{ borderColor: '#CFE8E0', backgroundColor: 'var(--bg-2)', color: 'var(--ink)' }}
                />
                <button
                  onClick={() => onTextSubmit?.(text)}
                  disabled={!text.trim()}
                  className="w-full mt-4 py-3.5 rounded-xl font-bold text-base text-white transition disabled:opacity-40"
                  style={{ backgroundColor: 'var(--rust)' }}
                >
                  Simplify this notice
                </button>
              </div>
            )}

            {error && (
              <div className="mt-5 text-sm font-semibold px-4 py-3 rounded-xl flex items-start gap-2" style={{ backgroundColor: 'var(--danger-tint)', color: 'var(--danger)' }}>
                <span className="mt-0.5">•</span>
                <span>{error}</span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default UploadScreen;