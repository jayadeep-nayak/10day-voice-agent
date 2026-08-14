'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Track } from 'livekit-client';
import { AnimatePresence, motion } from 'motion/react';
import {
  useAgent,
  useLocalParticipant,
  useSessionContext,
  useSessionMessages,
} from '@livekit/components-react';
import { AgentChatTranscript } from '@/components/agents-ui/agent-chat-transcript';
import {
  AgentControlBar,
  type AgentControlBarControls,
} from '@/components/agents-ui/agent-control-bar';

interface ZenithOverlayProps {
  onDisconnect?: () => void;
  supportsChatInput?: boolean;
  messages?: import('@livekit/components-react').ReceivedMessage[];
}

/** Floating math symbol particle */
function MathParticle({
  symbol,
  style,
}: {
  symbol: string;
  style: React.CSSProperties;
}) {
  return (
    <span
      className="absolute select-none pointer-events-none font-bold text-amber-400/20 animate-zenith-float"
      style={style}
    >
      {symbol}
    </span>
  );
}

const MATH_SYMBOLS = [
  '∑', '∫', 'π', '√', '∞', '±', '÷', '×', '≠', '≤', '≥',
  '²', '³', 'θ', 'Δ', 'λ', '%', '=', '+', '−',
];

/** Deterministic particle positions so they don't re-randomise on re-render */
const PARTICLES = MATH_SYMBOLS.map((sym, i) => ({
  sym,
  top: `${5 + ((i * 31) % 85)}%`,
  left: `${3 + ((i * 47) % 90)}%`,
  fontSize: `${14 + (i % 5) * 6}px`,
  animationDelay: `${(i * 0.6) % 4}s`,
  animationDuration: `${6 + (i % 4) * 2}s`,
}));

export function ZenithOverlay({
  onDisconnect,
  supportsChatInput = true,
  messages: externalMessages,
}: ZenithOverlayProps) {
  const session = useSessionContext();
  const sessionMessagesHook = useSessionMessages(externalMessages ? undefined : session);
  const messages = externalMessages ?? sessionMessagesHook.messages;
  const { state: agentState } = useAgent();
  const { localParticipant } = useLocalParticipant();
  const [chatOpen, setChatOpen] = useState(false);
  const [callSeconds, setCallSeconds] = useState(0);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setInterval(() => setCallSeconds((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const last = messages.at(-1);
    if (scrollAreaRef.current && last?.from?.isLocal) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const formatTimer = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
  };

  const micPublication = localParticipant.getTrackPublication(Track.Source.Microphone);
  const isMicMuted = !micPublication || micPublication.isMuted;

  const controls: AgentControlBarControls = {
    leave: true,
    microphone: true,
    chat: supportsChatInput,
    camera: false,
    screenShare: false,
  };

  const getStateInfo = () => {
    if (isMicMuted) {
      return {
        status: 'Microphone muted',
        subtitle: "Unmute to answer Zenith's question",
        badgeClass: 'border-red-500/40 bg-red-500/10 text-red-400',
        dot: <span className="h-2.5 w-2.5 rounded-full bg-red-500 animate-pulse" />,
      };
    }
    if (agentState === 'speaking') {
      return {
        status: 'Zenith is speaking',
        subtitle: 'Listen carefully and get ready to answer...',
        badgeClass: 'border-amber-500/50 bg-amber-500/15 text-amber-300 shadow-lg shadow-amber-500/25',
        dot: (
          <span className="flex items-center gap-0.5">
            {[1, 2, 3, 4, 5].map((n) => (
              <span
                key={n}
                className="w-0.5 rounded-full bg-current animate-wave-bar-1"
                style={{ height: `${12 + n * 2}px`, animationDelay: `${n * 0.1}s` }}
              />
            ))}
          </span>
        ),
      };
    }
    if (agentState === 'thinking') {
      return {
        status: 'Zenith is thinking',
        subtitle: 'Calculating the perfect problem...',
        badgeClass: 'border-violet-500/40 bg-violet-500/15 text-violet-400 shadow-lg shadow-violet-500/20',
        dot: <span className="h-2.5 w-2.5 rounded-full border-2 border-violet-400 border-t-transparent animate-ln-spin" />,
      };
    }
    if (agentState === 'initializing' || agentState === 'connecting') {
      return {
        status: 'Zenith is joining',
        subtitle: 'Setting up your maths session...',
        badgeClass: 'border-amber-400/40 bg-amber-400/10 text-amber-400',
        dot: <span className="h-2.5 w-2.5 rounded-full border-2 border-amber-400 border-t-transparent animate-ln-spin" />,
      };
    }
    return {
      status: 'Listening to you',
      subtitle: "Go ahead — answer Zenith's question!",
      badgeClass: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400 shadow-lg shadow-emerald-500/20',
      dot: <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-dot-pulse" />,
    };
  };

  const stateInfo = getStateInfo();

  const handleDisconnect = () => {
    session.end();
    onDisconnect?.();
  };

  return (
    <motion.div
      key="zenith-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.55, ease: 'easeOut' }}
      className="fixed inset-0 z-[200] overflow-hidden"
      style={{
        background:
          'linear-gradient(135deg, #07040f 0%, #0c0814 40%, #0a0710 70%, #07040f 100%)',
      }}
    >
      {/* ── Ambient background glow orbs ── */}
      <div className="pointer-events-none absolute inset-0">
        <div
          className="absolute rounded-full blur-3xl"
          style={{
            top: '-10%',
            right: '-5%',
            width: '55%',
            height: '55%',
            background:
              'radial-gradient(circle, rgba(245,158,11,0.12) 0%, transparent 70%)',
          }}
        />
        <div
          className="absolute rounded-full blur-3xl"
          style={{
            bottom: '-10%',
            left: '-5%',
            width: '50%',
            height: '50%',
            background:
              'radial-gradient(circle, rgba(139,92,246,0.10) 0%, transparent 70%)',
          }}
        />
        <div
          className="absolute rounded-full blur-3xl"
          style={{
            top: '30%',
            left: '25%',
            width: '50%',
            height: '40%',
            background:
              'radial-gradient(circle, rgba(251,191,36,0.06) 0%, transparent 70%)',
          }}
        />
      </div>

      {/* ── Floating math symbol particles ── */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {PARTICLES.map((p, i) => (
          <MathParticle
            key={i}
            symbol={p.sym}
            style={{
              top: p.top,
              left: p.left,
              fontSize: p.fontSize,
              animationDelay: p.animationDelay,
              animationDuration: p.animationDuration,
            }}
          />
        ))}
      </div>

      {/* ── Subtle amber dot-grid pattern ── */}
      <div
        className="pointer-events-none absolute inset-0 opacity-25"
        style={{
          backgroundImage:
            'radial-gradient(rgba(245,158,11,0.07) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      {/* ── Expanding energy rings (visible when chat closed) ── */}
      {!chatOpen && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div
            className="absolute rounded-full"
            style={{
              width: 340,
              height: 340,
              border: '1px solid rgba(245,158,11,0.15)',
              animation: 'zenith-ring-1 3.5s ease-out infinite',
            }}
          />
          <div
            className="absolute rounded-full"
            style={{
              width: 500,
              height: 500,
              border: '1px solid rgba(139,92,246,0.10)',
              animation: 'zenith-ring-2 3.5s ease-out infinite 1.2s',
            }}
          />
        </div>
      )}

      {/* ── MAIN CONTENT ── */}
      <div className="relative z-10 flex h-full flex-col justify-between pt-20 pb-6">

        {/* ── Top Status Header ── */}
        <div className="flex flex-col items-center justify-center text-center px-4 pt-1 pointer-events-none">
          <AnimatePresence mode="wait">
            <motion.div
              key={stateInfo.status}
              initial={{ opacity: 0, y: -12, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 12, scale: 0.95 }}
              transition={{ duration: 0.35, ease: 'easeOut' }}
              className="flex flex-col items-center pointer-events-auto"
            >
              {/* Session pill */}
              <div className="mb-2 flex items-center gap-2 rounded-full border border-amber-500/25 bg-amber-500/8 px-4 py-1 text-[11px] font-mono font-semibold text-amber-300 backdrop-blur-md shadow-sm">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
                <span className="tracking-widest uppercase">⚡ Zenith · Maths Specialist</span>
                <span className="text-amber-500/40">•</span>
                <span>{formatTimer(callSeconds)}</span>
              </div>

              {/* State badge */}
              <div
                className={`flex items-center gap-2.5 rounded-full px-5 py-2 text-xs font-bold tracking-wider uppercase backdrop-blur-xl border transition-all duration-300 mb-1.5 hover:scale-[1.03] ${stateInfo.badgeClass}`}
              >
                {stateInfo.dot}
                <span>{stateInfo.status}</span>
              </div>

              {/* Subtitle */}
              <p className="text-amber-200/45 text-xs md:text-sm font-medium tracking-wide">
                {stateInfo.subtitle}
              </p>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* ── Zenith Orb (only when chat closed) ── */}
        {!chatOpen && (
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.6, ease: 'easeOut', delay: 0.1 }}
            className="pointer-events-none flex items-center justify-center"
          >
            <div
              className="relative flex items-center justify-center"
              style={{ width: 220, height: 220 }}
            >
              {/* Glow blob */}
              <div
                className="absolute rounded-full blur-2xl"
                style={{
                  width: 200,
                  height: 200,
                  background:
                    'radial-gradient(circle, rgba(245,158,11,0.28) 0%, transparent 70%)',
                  animation: 'zenith-orb-glow 4s ease-in-out infinite',
                }}
              />
              {/* Outer orbit ring */}
              <div
                className="absolute rounded-full"
                style={{
                  width: 182,
                  height: 182,
                  border: '1px solid rgba(245,158,11,0.30)',
                  animation: 'spin-slow 20s linear infinite',
                }}
              >
                <span
                  className="absolute rounded-full"
                  style={{
                    width: 10,
                    height: 10,
                    background: '#f59e0b',
                    boxShadow: '0 0 14px 5px rgba(245,158,11,0.8)',
                    top: -5,
                    left: '50%',
                    transform: 'translateX(-50%)',
                  }}
                />
                <span
                  className="absolute rounded-full"
                  style={{
                    width: 7,
                    height: 7,
                    background: '#a78bfa',
                    boxShadow: '0 0 10px 3px rgba(167,139,250,0.7)',
                    bottom: -3.5,
                    left: '50%',
                    transform: 'translateX(-50%)',
                  }}
                />
              </div>
              {/* Inner dashed orbit ring */}
              <div
                className="absolute rounded-full"
                style={{
                  width: 148,
                  height: 148,
                  border: '1px dashed rgba(139,92,246,0.35)',
                  animation: 'spin-reverse-slow 15s linear infinite',
                }}
              />
              {/* Main Zenith sphere */}
              <div
                className="relative flex items-center justify-center rounded-full"
                style={{
                  width: 120,
                  height: 120,
                  background:
                    'linear-gradient(135deg, #78350f 0%, #b45309 30%, #d97706 60%, #7c3aed 100%)',
                  boxShadow:
                    '0 0 50px 15px rgba(245,158,11,0.30), 0 0 80px 30px rgba(139,92,246,0.15), inset 0 2px 0 rgba(255,255,255,0.20)',
                  animation: 'zenith-core-pulse 3.5s ease-in-out infinite',
                  border: '2px solid rgba(255,255,255,0.22)',
                }}
              >
                {/* Glass highlight */}
                <div
                  className="absolute inset-2 rounded-full"
                  style={{
                    background:
                      'linear-gradient(135deg, rgba(255,255,255,0.22) 0%, transparent 60%)',
                  }}
                />
                {/* Z logo */}
                <span
                  className="relative z-10 select-none font-black text-white"
                  style={{
                    fontSize: 44,
                    textShadow: '0 0 24px rgba(255,255,255,0.5)',
                    letterSpacing: '-2px',
                  }}
                >
                  Z
                </span>
              </div>
            </div>
          </motion.div>
        )}

        {/* ── Zenith name tag ── */}
        {!chatOpen && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="pointer-events-none flex flex-col items-center gap-1"
          >
            <h2
              className="font-black tracking-tight animate-pulse"
              style={{
                fontSize: 38,
                background:
                  'linear-gradient(135deg, #fbbf24 0%, #f59e0b 40%, #d97706 70%, #a78bfa 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              ZENITH
            </h2>
            <p className="text-amber-400/70 text-[10px] font-bold tracking-widest uppercase mb-4">
              Maths Practice Specialist
            </p>

            {/* ── Premium Advanced Workspace Panel ── */}
            <div className="flex flex-col sm:flex-row gap-4 w-full max-w-2xl px-6 pointer-events-auto">
              {/* Card 1: Live Scratchpad / Workspace */}
              <div
                className="flex-1 rounded-2xl p-4 border border-amber-500/20 backdrop-blur-md"
                style={{
                  background: 'rgba(12, 8, 20, 0.65)',
                  boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
                }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[10px] bg-amber-500/20 text-amber-300 font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
                    Formula Workspace
                  </span>
                </div>
                <div className="font-mono text-xs text-amber-200/65 space-y-1.5">
                  <div className="flex justify-between items-center bg-amber-500/5 px-2 py-1 rounded">
                    <span>Quadratic formula:</span>
                    <span className="text-amber-400 font-semibold">x = (-b±√Δ)/2a</span>
                  </div>
                  <div className="flex justify-between items-center bg-amber-500/5 px-2 py-1 rounded">
                    <span>Pythagorean theorem:</span>
                    <span className="text-amber-400 font-semibold">a² + b² = c²</span>
                  </div>
                  <div className="flex justify-between items-center bg-amber-500/5 px-2 py-1 rounded">
                    <span>Area of circle:</span>
                    <span className="text-amber-400 font-semibold">A = πr²</span>
                  </div>
                </div>
              </div>

              {/* Card 2: Zenith Analytics */}
              <div
                className="flex-1 rounded-2xl p-4 border border-violet-500/20 backdrop-blur-md"
                style={{
                  background: 'rgba(12, 8, 20, 0.65)',
                  boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
                }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[10px] bg-violet-500/20 text-violet-300 font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
                    Zenith Engine
                  </span>
                </div>
                <div className="font-mono text-xs text-violet-200/60 space-y-1">
                  <div className="flex justify-between border-b border-violet-500/10 pb-1">
                    <span>Practice Mode:</span>
                    <span className="text-violet-400 font-bold">Grade Adaptive</span>
                  </div>
                  <div className="flex justify-between border-b border-violet-500/10 pb-1">
                    <span>Methodology:</span>
                    <span className="text-violet-400 font-bold">Step-by-Step Drill</span>
                  </div>
                  <div className="flex justify-between pb-0.5">
                    <span>Target Accuracy:</span>
                    <span className="text-violet-400 font-bold">95%+</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* ── Chat Transcript ── */}
        <div className="absolute top-36 bottom-[140px] z-30 flex w-full flex-col pointer-events-auto">
          <AnimatePresence>
            {chatOpen && (
              <motion.div
                key="zenith-chat"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="flex h-full w-full flex-col"
              >
                <AgentChatTranscript
                  agentState={agentState}
                  messages={messages}
                  className="mx-auto w-full max-w-2xl [&_.is-user>div]:rounded-[22px] [&>div>div]:px-4 [&>div>div]:pt-4 md:[&>div>div]:px-6"
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* ── Bottom Control Bar ── */}
        <motion.div
          initial={{ opacity: 0, y: '100%' }}
          animate={{ opacity: 1, y: '0%' }}
          transition={{ duration: 0.3, delay: 0.2, ease: 'easeOut' }}
          className="relative z-50 mx-auto w-full max-w-lg px-4 flex flex-col gap-3"
        >
          {messages.length === 0 && !chatOpen && (
            <p className="text-center text-xs font-semibold text-amber-400/55 animate-pulse">
              ⚡ Zenith is ready — go ahead, speak your answer...
            </p>
          )}

          {/* Amber-themed glassmorphism control bar */}
          <div
            className="rounded-full p-2.5 transition-all duration-300"
            style={{
              background: 'rgba(12, 8, 20, 0.90)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              border: '1px solid rgba(245,158,11,0.28)',
              boxShadow:
                '0 10px 30px -5px rgba(0,0,0,0.8), 0 0 25px 0 rgba(245,158,11,0.18)',
            }}
          >
            <AgentControlBar
              variant="livekit"
              controls={controls}
              isChatOpen={chatOpen}
              isConnected={session.isConnected}
              onDisconnect={handleDisconnect}
              onIsChatOpenChange={setChatOpen}
            />
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
