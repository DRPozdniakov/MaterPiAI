import { useState } from "react";
import topBg from "@/assets/top-bg.png";
import bottomBg from "@/assets/bottom-bg.png";
import PricingCards from "../components/PricingCards";
import MockCheckout from "../components/MockCheckout";
import CirclePlayer from "../components/CirclePlayer";
import { analyzeVideo, createJob, type AnalyzeResponse, type TierCost } from "@/api";

const YOUTUBE_REGEX = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)/;

function extractVideoId(url: string): string | null {
  const match = url.match(/(?:v=|youtu\.be\/|shorts\/)([a-zA-Z0-9_-]{11})/);
  return match ? match[1] : null;
}

const LANGUAGES = [
  { code: "en", name: "English", short: "EN", flag: "\u{1F1EC}\u{1F1E7}" },
  { code: "es", name: "Spanish", short: "ES", flag: "\u{1F1EA}\u{1F1F8}" },
  { code: "fr", name: "French", short: "FR", flag: "\u{1F1EB}\u{1F1F7}" },
  { code: "de", name: "German", short: "DE", flag: "\u{1F1E9}\u{1F1EA}" },
  { code: "it", name: "Italian", short: "IT", flag: "\u{1F1EE}\u{1F1F9}" },
  { code: "pt", name: "Portuguese", short: "PT", flag: "\u{1F1F5}\u{1F1F9}" },
  { code: "nl", name: "Dutch", short: "NL", flag: "\u{1F1F3}\u{1F1F1}" },
  { code: "pl", name: "Polish", short: "PL", flag: "\u{1F1F5}\u{1F1F1}" },
];

type AppPhase = "input" | "checkout" | "player";

const Index = () => {
  const [url, setUrl] = useState("");
  const [selectedLang, setSelectedLang] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  // Data from backend
  const [videoData, setVideoData] = useState<AnalyzeResponse | null>(null);

  // Payment & player state
  const [phase, setPhase] = useState<AppPhase>("input");
  const [checkoutOption, setCheckoutOption] = useState<{ tier: string; name: string; total: string } | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);

  const isValidUrl = YOUTUBE_REGEX.test(url);
  const videoId = extractVideoId(url);
  const showPricing = phase === "input" && videoData !== null && selectedLang !== null;

  const handleLanguageClick = async (code: string) => {
    setSelectedLang(code);
    setVideoData(null);
    setAnalyzeError(null);

    if (!isValidUrl) return;

    setIsAnalyzing(true);
    try {
      const result = await analyzeVideo(url);
      setVideoData(result);
    } catch (err: any) {
      setAnalyzeError(err.message || "Analysis failed");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handlePricingSelect = (option: { tier: string; name: string; total: string }) => {
    setCheckoutOption(option);
    setPhase("checkout");
  };

  const handlePaymentSuccess = async () => {
    if (!checkoutOption || !selectedLang) return;

    setJobError(null);
    try {
      const job = await createJob(url, checkoutOption.tier, selectedLang);
      setJobId(job.job_id);
      setPhase("player");
      setCheckoutOption(null);
    } catch (err: any) {
      setJobError(err.message || "Job creation failed");
      setPhase("input");
      setCheckoutOption(null);
    }
  };

  const handleReset = () => {
    setUrl("");
    setSelectedLang(null);
    setVideoData(null);
    setAnalyzeError(null);
    setPhase("input");
    setCheckoutOption(null);
    setJobId(null);
    setJobError(null);
  };

  const formatDuration = (seconds: number): string => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}h ${m}m ${s}s`;
    return `${m}m ${s}s`;
  };

  // Circle layout
  const RADIUS = 170;
  const RADIUS_MOBILE = 110;

  return (
    <div className="min-h-screen relative corner-rosettes">
      {/* Hero — top mosaic peeking from top, fading down */}
      <header className="relative overflow-hidden z-10">
        <div className="absolute inset-0 bg-cover bg-top bg-no-repeat" style={{ backgroundImage: `url(${topBg})` }} />
        <div className="absolute inset-0 bg-gradient-to-b from-background/50 via-background/30 to-background" />
        <div className="relative z-10 max-w-4xl mx-auto px-6 pt-16 pb-12 text-center">
          <div className="flex items-center justify-center gap-4 mb-5">
            <span className="text-gold text-2xl">{"\u2619"}</span>
            <span className="font-display text-sm md:text-base text-gold tracking-[0.35em] uppercase">MasterPiAi</span>
            <span className="text-gold text-2xl">{"\u2767"}</span>
          </div>
          <p className="font-body text-lg text-muted-foreground italic font-bold max-w-md mx-auto">
            {phase === "player"
              ? "Your translation is being prepared."
              : "Paste a video link in the center, then select the language for your translation."}
          </p>
        </div>
      </header>

      {/* Circular Widget */}
      <main className="relative z-20 -mt-4 pb-24">
        <div className="flex flex-col items-center">
          {/* The circular dial */}
          <div className="relative w-[340px] h-[340px] md:w-[460px] md:h-[460px]">

            {/* Outer decorative ring */}
            <div className="absolute inset-0 rounded-full border-2 border-gold/30" />
            <div className="absolute inset-[4px] rounded-full border border-wine/20" />
            <div className="absolute inset-[8px] rounded-full braid-ring" />
            <div className="absolute inset-[20px] rounded-full border border-gold/15" />
            <div className="absolute inset-[22px] rounded-full border border-wine/10" />
            <div className="absolute inset-0 rounded-full medallion-rings" />

            {/* Tick marks between buttons */}
            {phase === "input" && [...Array(8)].map((_, i) => {
              const angle = (i * 45 + 22.5) * (Math.PI / 180);
              const r = 155;
              const x = Math.cos(angle) * r;
              const y = Math.sin(angle) * r;
              return (
                <div
                  key={`tick-${i}`}
                  className="absolute w-1 h-1 bg-gold/30 rotate-45"
                  style={{
                    left: `calc(50% + ${x}px - 2px)`,
                    top: `calc(50% + ${y}px - 2px)`,
                  }}
                />
              );
            })}

            {/* Language buttons around the circle */}
            {phase === "input" && LANGUAGES.map((lang, i) => {
              const angle = (i * 45 - 90) * (Math.PI / 180);
              const isSelected = selectedLang === lang.code;

              return (
                <button
                  key={lang.code}
                  onClick={() => handleLanguageClick(lang.code)}
                  className={`absolute z-10 flex flex-col items-center justify-center transition-all duration-300 group
                    w-16 h-16 md:w-[72px] md:h-[72px] rounded-full border-2 cursor-pointer
                    ${isSelected
                      ? "bg-primary text-primary-foreground border-gold shadow-[0_0_20px_hsl(42_70%_55%/0.4)] scale-110"
                      : "parchment-card border-gold/40 text-foreground hover:border-gold hover:shadow-[0_0_16px_hsl(42_70%_55%/0.25)] hover:scale-110"
                    }`}
                  style={{
                    left: `calc(50% + ${Math.cos(angle) * RADIUS_MOBILE}px - 32px)`,
                    top: `calc(50% + ${Math.sin(angle) * RADIUS_MOBILE}px - 32px)`,
                  }}
                  title={lang.name}
                >
                  <span className="text-lg leading-none">{lang.flag}</span>
                  <span className="font-display text-[10px] font-bold tracking-wider mt-0.5">{lang.short}</span>
                  <span className="absolute -bottom-7 left-1/2 -translate-x-1/2 text-xs font-body text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                    {lang.name}
                  </span>
                </button>
              );
            })}

            {/* Center area */}
            <div className="absolute inset-[55px] md:inset-[65px] rounded-full parchment-card border-2 border-gold/40 flex flex-col items-center justify-center p-4 shadow-inner overflow-hidden">
              <div className="absolute inset-1 rounded-full border border-gold/10 pointer-events-none" />

              {phase === "player" && jobId ? (
                <CirclePlayer jobId={jobId} onReset={handleReset} />
              ) : isAnalyzing ? (
                <div className="flex flex-col items-center gap-3 animate-pulse">
                  <svg className="animate-spin h-8 w-8 text-gold" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <span className="font-display text-sm text-gold italic">Consulting<br/>the Oracle...</span>
                </div>
              ) : isValidUrl && videoId ? (
                <div className="relative w-[140px] h-[140px] md:w-[160px] md:h-[160px] rounded-full overflow-hidden flex items-center justify-center group cursor-pointer"
                  onClick={() => { setUrl(""); setVideoData(null); setSelectedLang(null); setAnalyzeError(null); }}
                  title="Click to clear"
                >
                  <img
                    src={videoData?.video.thumbnail_url || `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`}
                    alt="Video thumbnail"
                    className="absolute inset-0 w-full h-full object-cover scale-[1.3]"
                  />
                  <div className="absolute inset-0 bg-gradient-to-b from-background/10 via-transparent to-background/40" />
                  <div className="absolute inset-0 border-4 border-gold/20 rounded-full" />
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-background/50">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gold">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center">
                  <input
                    type="url"
                    value={url}
                    onChange={(e) => { setUrl(e.target.value); setVideoData(null); setSelectedLang(null); setAnalyzeError(null); }}
                    placeholder="Paste URL"
                    className="w-[140px] h-[140px] md:w-[160px] md:h-[160px] rounded-full text-center px-4 bg-background/80 border-2 border-gold/30 font-body text-sm text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:border-gold transition-colors"
                  />
                  {!isValidUrl && url.length > 0 && (
                    <span className="text-destructive text-xs mt-2 font-body absolute -bottom-1">Invalid link</span>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Video info block — from real API data */}
          {videoData && !isAnalyzing && phase === "input" && (
            <div className="mt-8 max-w-md mx-auto animate-fade-in-up text-center">
              <p className="font-body text-lg text-muted-foreground italic">
                Video: <span className="text-gold font-bold">{videoData.video.title}</span>
              </p>
              <p className="font-body text-lg text-muted-foreground italic">
                Channel: <span className="text-gold font-bold">{videoData.video.channel}</span>
              </p>
              <p className="font-body text-lg text-muted-foreground italic">
                Duration: <span className="text-gold font-bold">{formatDuration(videoData.video.duration_seconds)}</span>
              </p>
            </div>
          )}

          {/* Error messages */}
          {analyzeError && (
            <div className="mt-4 text-center animate-fade-in-up">
              <span className="font-body text-sm text-destructive">{analyzeError}</span>
            </div>
          )}
          {jobError && (
            <div className="mt-4 text-center animate-fade-in-up">
              <span className="font-body text-sm text-destructive">{jobError}</span>
            </div>
          )}
        </div>

        {/* Pricing — from real tier data */}
        {showPricing && videoData && (
          <div className="max-w-4xl mx-auto px-4 mt-12 animate-fade-in-up">
            <div className="text-center mb-10">
              <div className="laurel-divider mb-4">
                <span className="text-gold text-2xl">{"\u269C"}</span>
              </div>
              <p className="font-body text-lg text-muted-foreground italic font-bold max-w-md mx-auto">
                Tap on the desired option below.
              </p>
              <div className="flex justify-center mt-3">
                <div className="flex gap-1">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className={`w-1.5 h-1.5 rotate-45 ${i === 2 ? 'bg-gold' : 'bg-gold/30'}`} />
                  ))}
                </div>
              </div>
            </div>
            <PricingCards tiers={videoData.tiers} onSelect={handlePricingSelect} />
          </div>
        )}

        {/* Footer — bottom mosaic peeking from bottom, fading up */}
        <footer className="relative overflow-hidden mt-24">
          <div className="absolute inset-0 bg-cover bg-bottom bg-no-repeat" style={{ backgroundImage: `url(${bottomBg})` }} />
          <div className="absolute inset-0 bg-gradient-to-t from-background/50 via-background/30 to-background" />
          <div className="relative z-10 max-w-3xl mx-auto px-4 pt-16 pb-20 text-center">
            <div className="laurel-divider mb-6 max-w-xs mx-auto">
              <span className="text-gold/60">{"\u2619"} {"\u2767"}</span>
            </div>
            <div className="flex items-center justify-center gap-4">
              <span className="text-gold text-xl">{"\u2619"}</span>
              <span className="font-display text-xs text-gold/60 tracking-[0.3em] uppercase">MasterPiAi {"\u00B7"} MMXXVI</span>
              <span className="text-gold text-xl">{"\u2767"}</span>
            </div>
          </div>
        </footer>
      </main>

      {/* Checkout Modal */}
      {phase === "checkout" && checkoutOption && (
        <MockCheckout
          optionName={checkoutOption.name}
          total={checkoutOption.total}
          onSuccess={handlePaymentSuccess}
          onCancel={() => setPhase("input")}
        />
      )}

      {/* Responsive overrides for language button positioning */}
      {phase === "input" && (
        <style>{`
          @media (min-width: 768px) {
            ${LANGUAGES.map((_, i) => {
              const angle = (i * 45 - 90) * (Math.PI / 180);
              return `button[title="${LANGUAGES[i].name}"] {
                left: calc(50% + ${Math.cos(angle) * RADIUS}px - 36px) !important;
                top: calc(50% + ${Math.sin(angle) * RADIUS}px - 36px) !important;
              }`;
            }).join('\n')}
          }
        `}</style>
      )}
    </div>
  );
};

export default Index;
