import { useState } from "react";

const LANGUAGES = [
  { code: "la", name: "Latin", flag: "🏛️" },
  { code: "es", name: "Spanish", flag: "🇪🇸" },
  { code: "fr", name: "French", flag: "🇫🇷" },
  { code: "de", name: "German", flag: "🇩🇪" },
  { code: "it", name: "Italian", flag: "🇮🇹" },
  { code: "pt", name: "Portuguese", flag: "🇵🇹" },
  { code: "ja", name: "Japanese", flag: "🇯🇵" },
  { code: "zh", name: "Chinese", flag: "🇨🇳" },
  { code: "ko", name: "Korean", flag: "🇰🇷" },
  { code: "ar", name: "Arabic", flag: "🇸🇦" },
  { code: "ru", name: "Russian", flag: "🇷🇺" },
  { code: "hi", name: "Hindi", flag: "🇮🇳" },
];

interface LanguageSelectorProps {
  selected: string;
  onSelect: (code: string) => void;
}

const LanguageSelector = ({ selected, onSelect }: LanguageSelectorProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const selectedLang = LANGUAGES.find((l) => l.code === selected);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-6 py-4 parchment-card border-2 border-gold/40 rounded-none font-body text-lg text-foreground hover:border-gold transition-all duration-300 group"
      >
        <span className="flex items-center gap-3">
          <span className="text-gold text-xl">☙</span>
          {selectedLang ? (
            <span className="font-semibold">
              {selectedLang.flag} {selectedLang.name}
            </span>
          ) : (
            <span className="text-muted-foreground italic">
              Select thy tongue...
            </span>
          )}
        </span>
        <svg
          className={`w-5 h-5 text-bronze transition-transform duration-300 ${isOpen ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute z-20 mt-1 w-full parchment-card border-2 border-gold/40 shadow-2xl max-h-72 overflow-y-auto">
          <div className="chevron-bar" />
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => { onSelect(lang.code); setIsOpen(false); }}
              className={`w-full text-left px-6 py-3 font-body text-lg transition-all duration-200 flex items-center gap-3 ${
                selected === lang.code
                  ? "bg-primary/10 text-wine font-bold"
                  : "text-foreground hover:bg-secondary/60"
              }`}
            >
              <span className="text-sm text-gold">{selected === lang.code ? "◆" : "◇"}</span>
              {lang.flag} {lang.name}
            </button>
          ))}
          <div className="chevron-bar" />
        </div>
      )}
    </div>
  );
};

export default LanguageSelector;
