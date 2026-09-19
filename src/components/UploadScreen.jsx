import { useState } from 'react';
import { Camera } from 'lucide-react';

const LANGUAGES = [
  { code: 'bn', label: 'বাংলা' },
  { code: 'te', label: 'తెలుగు' },
];

function UploadScreen({ onUpload, language, setLanguage, uploading, progress }) {
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = (file) => file && onUpload(file);
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-sm card p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: 'var(--teal)' }} />
            <span className="font-semibold text-sm">Notice, made simple</span>
          </div>
          {!uploading && (
            <div className="flex gap-1 bg-gray-100 rounded-full p-1">
              {LANGUAGES.map((l) => (
                <button
                  key={l.code}
                  onClick={() => setLanguage(l.code)}
                  aria-label={`Switch language to ${l.label}`}
                  aria-pressed={language === l.code}
                  className="text-xs px-2.5 py-1 rounded-full font-medium transition"
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
          )}
        </div>

        {uploading ? (
          <div className="py-10">
            <p className="text-center font-semibold mb-4">Uploading your notice...</p>
            <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
              <div className="h-full rounded-full transition-all" style={{ width: `${progress}%`, backgroundColor: 'var(--teal)' }} />
            </div>
            <p className="text-center text-xs mt-2" style={{ color: 'var(--ink-soft)' }}>{progress}%</p>
          </div>
        ) : (
          <>
            <h1 className="text-xl font-bold leading-snug mb-2">
              Show us the notice you can't understand
            </h1>
            <p className="text-sm mb-6" style={{ color: 'var(--ink-soft)' }}>
              We'll read it, simplify it, and read it out loud in {LANGUAGES.find(l => l.code === language)?.label}
            </p>

            <label
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              aria-label="Take or upload a photo of the notice"
              className="block border-2 border-dashed rounded-2xl py-10 text-center cursor-pointer transition"
              style={{ borderColor: isDragging ? 'var(--teal)' : '#CFE8E0', backgroundColor: isDragging ? 'var(--teal-tint)' : 'transparent' }}
            >
              <input type="file" accept="image/*" capture="environment" onChange={(e) => handleFile(e.target.files[0])} className="hidden" />
              <div className="w-14 h-14 mx-auto rounded-full flex items-center justify-center mb-3" style={{ backgroundColor: 'var(--teal-tint)' }}>
                <Camera size={24} color="var(--teal-dark)" />
              </div>
              <p className="font-semibold text-sm">Take or upload a photo</p>
              <p className="text-xs mt-1" style={{ color: 'var(--ink-soft)' }}>JPG, PNG or WEBP — or drag it here</p>
            </label>
          </>
        )}
      </div>
    </div>
  );
}

export default UploadScreen;