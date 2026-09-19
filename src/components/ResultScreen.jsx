import { useState } from 'react';
import { Calendar } from 'lucide-react';
import AudioPlayer from './AudioPlayer';
import { categoryStyle } from '../lib/categoryStyle';

function ResultScreen({ data, onReset, language, setLanguage }) {
  const [activeTab, setActiveTab] = useState('simplified');
  if (!data) return null;
  const style = categoryStyle(data.category);

  return (
    <div className="min-h-screen p-6 flex flex-col items-center gap-4">
      <div className="w-full max-w-sm card p-6">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs font-semibold tracking-wide" style={{ color: 'var(--ink-soft)' }}>
            SIMPLIFIED IN PLAIN LANGUAGE
          </p>
        </div>

        <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full mb-4"
          style={{ backgroundColor: style.bg, color: style.text }}>
          <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: style.dot }} />
          {data.category}
        </span>

        <div className="flex gap-5 mb-4 border-b" style={{ borderColor: '#EEF2F1' }} role="tablist">
          {[['simplified', 'Simplified Notice'], ['original', 'Original Document Text']].map(([key, label]) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              aria-selected={activeTab === key}
              role="tab"
              className="pb-2.5 text-xs font-semibold"
              style={{
                color: activeTab === key ? 'var(--teal-dark)' : 'var(--ink-soft)',
                borderBottom: activeTab === key ? '2px solid var(--teal)' : '2px solid transparent',
              }}
            >
              {label}
            </button>
          ))}
        </div>

        {activeTab === 'simplified' ? (
          <>
            <p className={`text-lg font-bold leading-relaxed mb-2 ${language === 'te' ? 'font-te' : 'font-bn'}`}>
              {data.simplified_summary}
            </p>
            <p className="text-sm mb-5" style={{ color: 'var(--ink-soft)' }}>
              For: <strong style={{ color: 'var(--ink)' }}>{data.target_audience}</strong>
            </p>

            {data.deadlines?.length > 0 && (
              <div className="flex items-center gap-2 mb-5 px-4 py-2.5 w-fit rounded-xl" style={{ backgroundColor: 'var(--danger-tint)', color: 'var(--danger)' }}>
                <Calendar size={16} />
                <span className="text-sm font-semibold">Compliance required by {data.deadlines[0]}</span>
              </div>
            )}

            <div className="rounded-xl p-4" style={{ backgroundColor: 'var(--amber-tint)' }}>
              <p className="text-xs font-bold mb-2.5 tracking-wide" style={{ color: 'var(--amber)' }}>WHAT TO DO</p>
              <ul className="space-y-2">
                {data.actionable_steps?.map((s, i) => (
                  <li key={i} className={`flex items-start gap-2 text-sm ${language === 'te' ? 'font-te' : 'font-bn'}`}>
                    <span className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold text-white mt-0.5" style={{ backgroundColor: 'var(--amber)' }}>
                      {i + 1}
                    </span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          </>
        ) : (
          <p className={`text-sm leading-relaxed p-4 rounded-xl ${language === 'te' ? 'font-te' : 'font-bn'}`} style={{ color: 'var(--ink-soft)', backgroundColor: '#F8FAF9' }}>
            {data.original_text}
          </p>
        )}

        <button onClick={onReset} className="w-full mt-5 py-3 rounded-xl font-semibold text-sm border transition hover:bg-gray-50" style={{ borderColor: '#E2E8F0', color: 'var(--ink-soft)' }}>
          Scan another notice
        </button>
      </div>

      <AudioPlayer audioUrl={data.audio_url} language={language} setLanguage={setLanguage} />
    </div>
  );
}

export default ResultScreen;