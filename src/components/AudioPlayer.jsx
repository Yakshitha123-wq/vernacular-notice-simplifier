import { useState, useRef, useEffect, useMemo } from 'react';
import { Play, Pause, Volume2 } from 'lucide-react';
import { API_BASE } from '../lib/api';

const LANGUAGES = [
  { code: 'bn', label: 'বাংলা' },
  { code: 'te', label: 'తెలుగు' },
];

const MAX_TTS_CHARS = 500;

function fmt(secs) {
  if (!Number.isFinite(secs)) return "0:00";
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

function AudioPlayer({ audioUrl, text = "", language = "bn", setLanguage }) {
  const [playing, setPlaying] = useState(false);
  const [time, setTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [ttsFailed, setTtsFailed] = useState(false);
  const [blobUrl, setBlobUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const audioRef = useRef(null);
  const synTimer = useRef(null);

  const langCode = language || 'bn';
  const ttsUrl = useMemo(() => {
    if (audioUrl || !text) return null;
    return `${API_BASE}/tts?language=${encodeURIComponent(langCode)}&text=${encodeURIComponent(text.slice(0, MAX_TTS_CHARS))}`;
  }, [audioUrl, langCode, text]);

  const src = audioUrl || (!ttsFailed ? blobUrl : null);
  const useSpeech = !src && !!text;

  useEffect(() => {
    let cancelled = false;
    let createdUrl = null;
    if (audioUrl || !ttsUrl) {
      setBlobUrl(null);
      setLoading(false);
      return undefined;
    }
    setLoading(true);
    (async () => {
      try {
        const res = await fetch(ttsUrl, { headers: { Accept: "audio/mpeg" } });
        if (!res.ok) throw new Error(`TTS failed (${res.status})`);
        const buf = await res.arrayBuffer();
        if (cancelled || !buf.byteLength) return;
        createdUrl = URL.createObjectURL(new Blob([buf], { type: "audio/mpeg" }));
        setBlobUrl(createdUrl);
      } catch {
        if (!cancelled) setTtsFailed(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
      if (createdUrl) URL.revokeObjectURL(createdUrl);
    };
  }, [ttsUrl, audioUrl]);

  const stopTick = () => {
    if (synTimer.current) {
      clearInterval(synTimer.current);
      synTimer.current = null;
    }
  };

  const speak = () => {
    const synth = window.speechSynthesis;
    if (!synth) return;
    const voices = synth.getVoices();
    const voice = voices.find((v) => v.lang.toLowerCase().startsWith(langCode)) || null;
    const utterance = new SpeechSynthesisUtterance(text);
    if (voice) utterance.voice = voice;
    utterance.lang = voice ? voice.lang : (langCode === 'te' ? 'te-IN' : 'bn-IN');
    utterance.onend = () => { setPlaying(false); setTime(0); };
    synth.cancel();
    setTimeout(() => synth.speak(utterance), 30);
    synTimer.current = setInterval(() => setTime((t) => t + 1), 1000);
  };

  const toggle = () => {
    if (useSpeech) {
      const synth = window.speechSynthesis;
      if (!synth) return;
      if (playing) {
        synth.pause();
        stopTick();
      } else {
        if (synth.paused) {
          synth.resume();
        } else {
          speak();
        }
        synTimer.current = setInterval(() => setTime((t) => t + 1), 1000);
      }
      setPlaying((p) => !p);
      return;
    }
    if (!audioRef.current) return;
    if (playing) {
      audioRef.current.pause();
    } else {
      audioRef.current.play()?.catch(() => {});
    }
    setPlaying((p) => !p);
  };

  useEffect(() => {
    window.speechSynthesis?.getVoices();
    return () => {
      stopTick();
      window.speechSynthesis?.cancel();
    };
  }, []);

  useEffect(() => {
    if (useSpeech && playing) {
      stopTick();
      window.speechSynthesis?.cancel();
      setTime(0);
      speak();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language, text]);

  if (!audioUrl && !text) return null;

  const elapsedPct = duration > 0 ? Math.min(100, (time / duration) * 100) : Math.min(100, (time / 120) * 100);
  const rightLabel = duration > 0 ? fmt(Math.max(0, duration - time)) : fmt(time);

  return (
    <div className="w-full max-w-sm card p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Volume2 size={16} style={{ color: 'var(--rust-dark)' }} />
          <p className="text-sm font-bold" style={{ color: 'var(--rust-dark)' }}>Tap to listen</p>
        </div>
        <div className="flex gap-1 bg-gray-100 rounded-full p-1">
          {LANGUAGES.map((l) => (
            <button
              key={l.code}
              onClick={() => setLanguage?.(l.code)}
              aria-label={`Switch audio to ${l.label}`}
              aria-pressed={language === l.code}
              className="text-sm px-2.5 py-1 rounded-full font-semibold"
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
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={toggle}
          disabled={loading || (!src && !useSpeech)}
          aria-label={playing ? "Pause audio" : "Play audio"}
          className="w-14 h-14 rounded-full flex items-center justify-center flex-shrink-0 transition disabled:opacity-50"
          style={{ backgroundColor: 'var(--rust)' }}
        >
          {loading ? (
            <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : playing ? (
            <Pause size={22} color="white" fill="white" />
          ) : (
            <Play size={22} color="white" fill="white" />
          )}
        </button>
        <div className="flex-1 h-2.5 rounded-full bg-gray-100 overflow-hidden" role="progressbar" aria-valuenow={Math.round(time)} aria-valuemax={Math.round(duration)}>
          <div className="h-full transition-all" style={{ width: `${elapsedPct}%`, backgroundColor: 'var(--rust)' }} />
        </div>
        <span className="text-sm font-semibold w-10 text-right" style={{ color: 'var(--ink-soft)' }}>{rightLabel}</span>
      </div>

      {src && (
        <audio
          ref={audioRef}
          key={src}
          src={src}
          preload="metadata"
          onTimeUpdate={(e) => setTime(e.currentTarget.currentTime)}
          onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
          onEnded={() => { setPlaying(false); setTime(0); }}
          onError={() => {
            if (!audioUrl) {
              setTtsFailed(true);
              setPlaying(false);
              setTime(0);
            }
          }}
          className="hidden"
        />
      )}
    </div>
  );
}

export default AudioPlayer;