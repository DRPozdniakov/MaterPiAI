import type { TierCost } from "@/api";

function fmt(value: number): string {
  if (value === 0) return "FREE";
  if (value < 0.01) return `$${value.toFixed(4)}`;
  return `$${value.toFixed(2)}`;
}

function fmtDuration(minutes: number): string {
  if (minutes >= 60) {
    const h = Math.floor(minutes / 60);
    const m = Math.round(minutes % 60);
    return `${h}h ${m}m`;
  }
  return `${Math.round(minutes)}m`;
}

function tierPercent(tier: string): string {
  if (tier === "short") return "12%";
  if (tier === "medium") return "40%";
  return "100%";
}

interface PricingCardsProps {
  tiers: TierCost[];
  onSelect?: (option: { tier: string; name: string; total: string }) => void;
}

const PricingCards = ({ tiers, onSelect }: PricingCardsProps) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
      {tiers.map((tier, i) => {
        const isFull = tier.tier === "full";
        const label = tier.tier.toUpperCase();
        const name = tier.tier.charAt(0).toUpperCase() + tier.tier.slice(1);
        const duration = fmtDuration(tier.duration_minutes);
        const margin = tier.total_cost - tier.stripe_fee - tier.transcription_cost - tier.translation_cost - tier.tts_cost;
        const marginDisplay = margin > 0 ? fmt(margin - (tier.transcription_cost + tier.translation_cost + tier.tts_cost) * 0) : "$0.00";

        // Recalculate margin as: subtotal * 0.25
        const subtotal = tier.transcription_cost + tier.translation_cost + tier.tts_cost;
        const marginAmt = subtotal * 0.25;

        return (
          <button
            key={tier.tier}
            onClick={() => onSelect?.({ tier: tier.tier, name, total: fmt(tier.total_cost) })}
            className={`relative flex flex-col text-left cursor-pointer group transition-all duration-500 hover:-translate-y-2 pt-4 pb-4
              ${isFull ? "md:scale-105 md:z-10" : ""}`}
            style={{ animationDelay: `${i * 150}ms` }}
          >
            <div
              className="scroll-paper flex-1 flex flex-col px-8 py-10 transition-all duration-300
                group-hover:shadow-[0_0_20px_hsl(42_70%_55%/0.15)]"
            >
              {/* Gold line accents on sides */}
              <div className="absolute top-4 bottom-4 left-0 w-[2px] transition-colors duration-300 bg-gold/20 group-hover:bg-gold/40" />
              <div className="absolute top-4 bottom-4 right-0 w-[2px] transition-colors duration-300 bg-gold/20 group-hover:bg-gold/40" />

              {isFull && (
                <div className="absolute top-6 right-4 z-10">
                  <span className="bg-primary text-primary-foreground px-3 py-1 font-display text-xs font-bold tracking-widest uppercase">
                    ✦ Complete ✦
                  </span>
                </div>
              )}

              {/* Header */}
              <h3 className="font-display text-2xl font-bold text-foreground tracking-wide mb-1">
                {label}
              </h3>
              <div className="flex items-baseline gap-3 mb-1">
                <span className="font-display text-lg text-gold font-bold">{duration}</span>
                <span className="font-body text-sm text-muted-foreground">({tierPercent(tier.tier)} of video)</span>
              </div>

              {/* Price breakdown */}
              <div className="relative mb-6 mt-4 py-4 border-y-2 border-gold/30">
                <span className="absolute -top-2 left-1/2 -translate-x-1/2 bg-card px-3 text-gold text-xs tracking-widest font-display">
                  PRETIUM
                </span>
                <ul className="space-y-2 mb-4 mt-1">
                  <li className="flex justify-between items-center font-body text-sm text-foreground/80">
                    <span>Transcription</span>
                    <span className="text-muted-foreground">{fmt(tier.transcription_cost)}</span>
                  </li>
                  <li className="flex justify-between items-center font-body text-sm text-foreground/80">
                    <span>Translation</span>
                    <span className="text-muted-foreground">{fmt(tier.translation_cost)}</span>
                  </li>
                  <li className="flex justify-between items-center font-body text-sm text-foreground/80">
                    <span>TTS</span>
                    <span className="text-muted-foreground">{fmt(tier.tts_cost)}</span>
                  </li>
                </ul>
                <div className="flex justify-between items-center pt-3 border-t border-gold/20 mb-2">
                  <span className="font-body text-sm text-foreground/60">Margin (25%)</span>
                  <span className="text-muted-foreground font-body text-sm">{fmt(marginAmt)}</span>
                </div>
                <div className="flex justify-between items-center mb-3">
                  <span className="font-body text-sm text-foreground/60">Stripe (2.9% + $0.30)</span>
                  <span className="text-muted-foreground font-body text-sm">{fmt(tier.stripe_fee)}</span>
                </div>
                <div className="flex justify-between items-center pt-3 border-t-2 border-gold/30">
                  <span className="font-display font-bold text-foreground">TOTAL</span>
                  <span className="font-display text-3xl font-bold text-wine">{fmt(tier.total_cost)}</span>
                </div>
                <p className="text-muted-foreground font-body text-xs mt-1 text-right">
                  for {duration}
                </p>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
};

export default PricingCards;
