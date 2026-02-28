import { useState, useRef, useEffect } from "react";
import { subscribeJobProgress, getAudioUrl, type SSEProgress } from "@/api";

interface CirclePlayerProps {
  jobId: string;
  onReset: () => void;
}

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

const CirclePlayer = ({ jobId, onReset }: CirclePlayerProps) => {
  const [phase, setPhase] = useState<"processing" | "ready" | "error">("processing");
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState("Starting...");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Audio playback
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [totalDuration, setTotalDuration] = useState(0);

  // SSE subscription
  useEffect(() => {
    const es = subscribeJobProgress(jobId);

    es.addEventListener("progress", (e) => {
      const data: SSEProgress = JSON.parse(e.data);
      setProgress(data.progress_pct);
      setStage(data.current_stage);

      if (data.status === "completed") {
        es.close();
        setPhase("ready");
      } else if (data.status === "failed") {
        es.close();
        setErrorMsg(data.error || "Pipeline failed");
        setPhase("error");
      }
    });

    es.addEventListener("timeout", () => {
      es.close();
      setErrorMsg("Connection timed out");
      setPhase("error");
    });

    es.onerror = () => {
      es.close();
      setErrorMsg("Connection lost");
      setPhase("error");
    };

    return () => es.close();
  }, [jobId]);

  // Load audio when ready
  useEffect(() => {
    if (phase !== "ready") return;
    const audio = new Audio(getAudioUrl(jobId));
    audioRef.current = audio;

    audio.addEventListener("loadedmetadata", () => {
      setTotalDuration(audio.duration);
    });
    audio.addEventListener("timeupdate", () => {
      setElapsed(audio.currentTime);
    });
    audio.addEventListener("ended", () => {
      setIsPlaying(false);
    });

    return () => {
      audio.pause();
      audio.src = "";
    };
  }, [phase, jobId]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleRestart = () => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = 0;
    setElapsed(0);
    setIsPlaying(false);
  };

  const clampedProgress = Math.min(progress, 100);
  const playProgress = totalDuration > 0 ? (elapsed / totalDuration) * 100 : 0;
  const circumference = 2 * Math.PI * 120;
  const strokeDashoffset = circumference - (circumference * clampedProgress) / 100;
  const playStrokeDashoffset = circumference - (circumference * playProgress) / 100;

  if (phase === "error") {
    return (
      <div className="flex flex-col items-center justify-center w-full h-full gap-3">
        <span className="font-display text-sm text-destructive">Failed</span>
        <span className="font-body text-xs text-muted-foreground text-center px-4">{errorMsg}</span>
        <button
          onClick={onReset}
          className="mt-2 px-4 py-1.5 rounded-full border border-gold/30 font-body text-xs text-gold hover:border-gold transition-colors cursor-pointer"
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center w-full h-full">
      {phase === "processing" ? (
        <>
          <svg className="w-[180px] h-[180px] md:w-[200px] md:h-[200px] -rotate-90" viewBox="0 0 260 260">
            <circle cx="130" cy="130" r="120" fill="none" stroke="hsl(var(--gold) / 0.15)" strokeWidth="6" />
            <circle
              cx="130" cy="130" r="120" fill="none"
              stroke="hsl(var(--gold))"
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className="transition-all duration-200"
            />
          </svg>
          <div className="absolute flex flex-col items-center gap-2">
            <svg className="animate-spin h-6 w-6 text-gold" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span className="font-display text-xs text-gold/70 italic">{stage}</span>
            <span className="font-display text-lg text-gold font-bold">{Math.round(clampedProgress)}%</span>
          </div>
        </>
      ) : (
        <>
          <svg className="w-[180px] h-[180px] md:w-[200px] md:h-[200px] -rotate-90" viewBox="0 0 260 260">
            <circle cx="130" cy="130" r="120" fill="none" stroke="hsl(var(--gold) / 0.15)" strokeWidth="6" />
            <circle
              cx="130" cy="130" r="120" fill="none"
              stroke="hsl(var(--gold))"
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={playStrokeDashoffset}
              className="transition-all duration-100"
            />
          </svg>
          <div className="absolute flex flex-col items-center gap-1 max-w-[160px]">
            <span className="font-display text-[10px] text-gold/70 tracking-wider uppercase text-center leading-tight">
              Audiobook
            </span>

            {/* Time */}
            <span className="font-display text-sm text-foreground font-bold tabular-nums">
              {formatTime(elapsed)} <span className="text-muted-foreground font-normal">/ {formatTime(totalDuration)}</span>
            </span>

            {/* Controls */}
            <div className="flex items-center gap-3 mt-1">
              {/* Restart */}
              <button
                onClick={handleRestart}
                className="w-8 h-8 rounded-full border border-gold/30 flex items-center justify-center hover:border-gold transition-colors cursor-pointer"
                title="Restart"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gold">
                  <polyline points="1 4 1 10 7 10" />
                  <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                </svg>
              </button>

              {/* Play/Pause */}
              <button
                onClick={togglePlay}
                className="w-12 h-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center hover:opacity-90 transition-opacity cursor-pointer"
              >
                {isPlaying ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="6" y="4" width="4" height="16" />
                    <rect x="14" y="4" width="4" height="16" />
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="8,4 20,12 8,20" />
                  </svg>
                )}
              </button>

              {/* New translation */}
              <button
                onClick={onReset}
                className="w-8 h-8 rounded-full border border-gold/30 flex items-center justify-center hover:border-gold transition-colors cursor-pointer"
                title="New translation"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gold">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

          </div>
        </>
      )}
    </div>
  );
};

export default CirclePlayer;
