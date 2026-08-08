import { Button } from '@/components/ui/button';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  isStarting?: boolean;
}

export const WelcomeView = ({
  startButtonText = 'Start Session',
  onStartCall,
  isStarting = false,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="relative min-h-svh bg-transparent">
      {/* Background ambient glow */}
      <div className="hero-glow pointer-events-none absolute inset-0" />

      <section className="relative flex min-h-svh flex-col items-center justify-center px-6 pt-20 pb-24 text-center">
        {/* ── Central AI Voice Sound Reactor Core (Preserved Electric Cyan-Blue Orb Animation) ── */}
        <div className="relative my-8 flex items-center justify-center">
          {/* Ambient Background Aura Glow */}
          <div className="animate-orb-glow absolute h-64 w-64 rounded-full bg-cyan-500/20 blur-3xl md:h-80 md:w-80" />

          {/* Outer Orbit Ring 1 (Clockwise Rotation with Glowing Node) */}
          <div className="animate-spin-slow absolute h-52 w-52 rounded-full border border-cyan-400/35 md:h-64 md:w-64">
            <span className="absolute -top-1.5 left-1/2 h-3.5 w-3.5 -translate-x-1/2 rounded-full bg-cyan-400 shadow-lg shadow-cyan-400/80" />
            <span className="absolute -bottom-1.5 left-1/2 h-2.5 w-2.5 -translate-x-1/2 rounded-full bg-blue-400 shadow-md shadow-blue-400/80" />
          </div>

          {/* Inner Orbit Ring 2 (Counter-clockwise Dashed Ring) */}
          <div className="animate-spin-reverse-slow absolute h-44 w-44 rounded-full border border-dashed border-cyan-300/30 md:h-52 md:w-52" />

          {/* Expanding Pulsing Ring 3 */}
          <div className="animate-ring-pulse absolute h-40 w-40 rounded-full border-2 border-cyan-400/30 md:h-48 md:w-48" />

          {/* Floating Energy Particles */}
          <div className="animate-subtle-float absolute -top-4 left-4 h-2 w-2 rounded-full bg-cyan-300 shadow-sm shadow-cyan-300" />
          <div className="animate-subtle-float absolute -bottom-2 right-6 h-2.5 w-2.5 rounded-full bg-blue-400 shadow-sm shadow-blue-400" />
          <div className="animate-subtle-float absolute top-12 -right-4 h-2 w-2 rounded-full bg-cyan-200 shadow-sm shadow-cyan-200" />

          {/* ── Main AI Voice Reactor Sphere Core (Electric Cyan-Blue) ── */}
          <div className="animate-ai-core-pulse relative flex h-36 w-36 items-center justify-center rounded-full bg-gradient-to-br from-cyan-400 via-blue-500 to-cyan-600 shadow-2xl shadow-cyan-500/40 md:h-44 md:w-44 border-2 border-white/40 backdrop-blur-xl">
            {/* Inner Glass Sphere Glow */}
            <div className="absolute inset-2 rounded-full bg-gradient-to-br from-white/30 via-transparent to-black/30 backdrop-blur-md" />

            {/* Inner AI Reactor Live Soundwave Equalizer */}
            <div className="relative z-10 flex items-center justify-center gap-1.5">
              <span className="w-1.5 rounded-full bg-white animate-core-eq-1 shadow-sm" />
              <span className="w-1.5 rounded-full bg-cyan-100 animate-core-eq-2 shadow-sm" />
              <span className="w-2 rounded-full bg-white animate-core-eq-3 shadow-sm" />
              <span className="w-1.5 rounded-full bg-cyan-100 animate-core-eq-4 shadow-sm" />
              <span className="w-1.5 rounded-full bg-white animate-core-eq-5 shadow-sm" />
            </div>
          </div>
        </div>

        {/* ── Hero Title ("Meet Nova") Matching User Image ── */}
        <h1 className="max-w-2xl text-4xl font-extrabold tracking-tight md:text-5xl lg:text-6xl drop-shadow-sm">
          <span className="text-[#FAF8F5]">Meet </span>
          <span className="text-[#38BDF8] drop-shadow">Nova</span>
        </h1>

        {/* Subtitle Matching User Image */}
        <p className="text-[#8E9BAE] mt-4 max-w-md text-base leading-7 md:text-lg font-normal">
          Your AI voice companion is ready to converse, practice, and learn with you.
        </p>

        {/* READY Status Indicator Badge (Dark Emerald Green Pill matching User Image) */}
        <div className="mt-6 mb-8 flex items-center gap-2 rounded-full border border-emerald-800/60 bg-[#072418] px-4 py-1.5 text-xs font-bold text-[#34D399] shadow-md shadow-emerald-950/40 backdrop-blur-md">
          <span className="h-2.5 w-2.5 rounded-full bg-[#34D399] animate-pulse shadow-sm shadow-[#34D399]" />
          <span className="tracking-widest uppercase">Ready</span>
        </div>

        {/* Start Session CTA Button (Dark Emerald Green Pill matching User Image) */}
        <Button
          size="lg"
          onClick={onStartCall}
          disabled={isStarting}
          id="nova-start-button"
          className="w-72 rounded-full bg-gradient-to-r from-[#0B3B2B] via-[#0D4B36] to-[#083827] hover:from-[#0E543D] hover:to-[#0B4431] px-8 py-6 text-base font-bold text-[#FAF8F5] border border-emerald-700/50 shadow-xl shadow-emerald-950/60 transition-all duration-300 hover:shadow-emerald-900/40 hover:scale-[1.03] active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isStarting ? (
            <span className="flex items-center gap-2 text-[#FAF8F5]">
              <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-ln-spin" />
              Connecting...
            </span>
          ) : (
            <span className="flex items-center gap-2 text-[#FAF8F5]">
              🎙 {startButtonText}
            </span>
          )}
        </Button>
      </section>
    </div>
  );
};
