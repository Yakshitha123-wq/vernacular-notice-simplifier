import { useState } from 'react';
import { Calendar, RotateCcw } from 'lucide-react';
import AudioPlayer from './AudioPlayer';
import { categoryStyle } from '../lib/categoryStyle';

function ResultScreen({ data, onReset, language, setLanguage }) {
  const [activeTab, setActiveTab] = useState('simplified');
  if (!data) return null;
  const style = categoryStyle(data.category);

  return (
    <div className="min-h-screen p-5 flex flex-col items-center gap-4">
      <AudioPlayer audioUrl={data.audio_url} text={data.simplified_summary} language={language} setLanguage={setLanguage} />

      <div className="w-full max-w-sm card p-6">
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-semibold" style={{ color: 'var(--ink-soft)' }}>
            Simplified in plain language
          </p>
        </div>

        <span className="inline-flex items-center gap-1.5 text-sm font-bold px-3 py-1.5 rounded-full mb-4"
          style={{ backgroundColor: style.bg, color: style.text }}>
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: style.dot }} />
          {data.category}
        </span>

        <div className="flex gap-5 mb-4 border-b" style={{ borderColor: '#EEF2F1' }} role="tablist">
          {[['simplified', 'Simple summary'], ['original', 'Original text']].map(([key, label]) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              aria-selected={activeTab === key}
              role="tab"
              className="pb-2.5 text-sm font-bold"
              style={{
                color: activeTab === key ? 'var(--rust-dark)' : 'var(--ink-soft)',
                borderBottom: activeTab === key ? '2px solid var(--rust)' : '2px solid transparent',
              }}
            >
              {label}
            </button>
          ))}
        </div>

        {activeTab === 'simplified' ? (
          <>
            <p className={`text-xl font-bold leading-relaxed mb-3 ${language === 'te' ? 'font-te' : 'font-bn'}`}>
              {data.simplified_summary}
            </p>
            <p className="text-base mb-5" style={{ color: 'var(--ink-soft)' }}>
              For: <strong style={{ color: 'var(--ink)' }}>{data.target_audience}</strong>
            </p>

            {data.deadlines?.length > 0 && (
              <div className="flex items-center gap-3 mb-5 px-4 py-3 w-fit rounded-xl" style={{ backgroundColor: 'var(--danger-tint)', color: 'var(--danger)' }}>
                <Calendar size={20} />
                <span className="text-base font-bold">Do this by {data.deadlines[0]}</span>
              </div>
            )}

            <div className="rounded-xl p-4" style={{ backgroundColor: 'var(--forest-tint)' }}>
              <p className="text-sm font-bold mb-3" style={{ color: 'var(--forest)' }}>What to do</p>
              <ul className="space-y-3">
                {data.actionable_steps?.map((s, i) => (
                  <li key={i} className={`flex items-start gap-3 text-base ${language === 'te' ? 'font-te' : 'font-bn'}`}>
                    <span className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white mt-0.5" style={{ backgroundColor: 'var(--forest)' }}>
                      {i + 1}
                    </span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          </>
        ) : (
          <p className={`text-base leading-relaxed p-4 rounded-xl ${language === 'te' ? 'font-te' : 'font-bn'}`} style={{ color: 'var(--ink-soft)', backgroundColor: '#F8FAF9' }}>
            {data.original_text}
          </p>
        )}

        <button onClick={onReset} className="w-full mt-6 py-3.5 rounded-xl font-bold text-base border flex items-center justify-center gap-2 transition hover:bg-gray-50" style={{ borderColor: '#E2E8F0', color: 'var(--ink-soft)' }}>
          <RotateCcw size={18} />
          Scan another notice
        </button>
      </div>
    </div>
  );
}

export default ResultScreen;