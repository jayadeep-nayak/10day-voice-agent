'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { RoomEvent } from 'livekit-client';
import { useAgent, useSessionContext, useSessionMessages } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';
import { ZenithOverlay } from '@/components/app/zenith-overlay';
import { Button } from '@/components/ui/button';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(AgentSessionView_01);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
    },
    hidden: {
      opacity: 0,
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.4,
    ease: 'easeInOut',
  },
};

interface ViewControllerProps {
  appConfig: AppConfig;
  onRestartSession?: () => void;
  autoStart?: boolean;
}

export function ViewController({
  appConfig,
  onRestartSession,
  autoStart = false,
}: ViewControllerProps) {
  const session = useSessionContext();
  const { isConnected, start, end, connectionState } = session;
  const { messages } = useSessionMessages(session);
  const agent = useAgent();
  const agentState = agent.state;
  const agentParticipant = agent.internal.agentParticipant;
  const { resolvedTheme } = useTheme();

  // Detect if Zenith (maths specialist) is the active agent with reactive events & messages
  const [isZenithActive, setIsZenithActive] = useState(false);

  useEffect(() => {
    const checkZenithState = () => {
      const p = agentParticipant;
      const attrs = (p?.attributes as Record<string, string>) ?? {};
      const idMatches =
        p?.identity?.toLowerCase().includes('zenith') ||
        p?.name?.toLowerCase().includes('zenith');
      const attrMatches =
        attrs.active_agent?.toLowerCase() === 'zenith' ||
        attrs.agent_name?.toLowerCase() === 'zenith';

      // Also check recent transcripts for handoff transition
      const hasHandoff = messages.some((m) => {
        const text = m.message?.toLowerCase() ?? '';
        return text.includes('zenith') || text.includes('maths practice specialist');
      });

      setIsZenithActive(Boolean(idMatches || attrMatches || hasHandoff));
    };

    checkZenithState();

    const room = session.room;
    if (!room) return;

    room.on(RoomEvent.ParticipantAttributesChanged, checkZenithState);
    room.on(RoomEvent.ParticipantMetadataChanged, checkZenithState);
    return () => {
      room.off(RoomEvent.ParticipantAttributesChanged, checkZenithState);
      room.off(RoomEvent.ParticipantMetadataChanged, checkZenithState);
    };
  }, [session.room, agentParticipant, messages]);

  const [isStarting, setIsStarting] = useState(false);
  const [micError, setMicError] = useState(false);
  const [callEnded, setCallEnded] = useState(false);
  const [showHowToEnable, setShowHowToEnable] = useState(false);

  // Wrap start to check microphone permission & handle connection flow
  const handleStart = useCallback(async () => {
    setMicError(false);
    setCallEnded(false);
    setShowHowToEnable(false);
    setIsStarting(true);

    try {
      // 1. Explicitly test microphone permission with getUserMedia
      if (typeof navigator !== 'undefined' && navigator.mediaDevices?.getUserMedia) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          // Stop preview track once permission is verified
          stream.getTracks().forEach((track) => track.stop());
        } catch (mediaErr: unknown) {
          console.warn('Microphone permission check failed:', mediaErr);
          setMicError(true);
          setIsStarting(false);
          return;
        }
      }

      // 2. Start LiveKit session
      await start();
    } catch (err: unknown) {
      console.error('Error starting session:', err);
      setMicError(true);
    } finally {
      setIsStarting(false);
    }
  }, [start]);

  // Detect disconnection / end session
  const handleEnd = useCallback(() => {
    end();
    setCallEnded(true);
    setIsStarting(false);
  }, [end]);

  const hasAutoStartedRef = useRef(false);
  const wasConnectedRef = useRef(false);

  // Track connection status & handle callEnded state transition
  useEffect(() => {
    if (isConnected) {
      wasConnectedRef.current = true;
      setCallEnded(false);
      setIsStarting(false);
    } else if (wasConnectedRef.current && !isConnected) {
      setCallEnded(true);
      setIsStarting(false);
    }
  }, [isConnected]);

  // Auto-start session only once on initial mount if autoStart is true
  useEffect(() => {
    if (autoStart && !hasAutoStartedRef.current && !isConnected && !isStarting && !callEnded) {
      hasAutoStartedRef.current = true;
      handleStart();
    }
  }, [autoStart, isConnected, isStarting, callEnded, handleStart]);

  // Determine if we are currently in "Connecting" state:
  // User clicked start OR room is connecting OR agent is initializing/connecting
  const isConnectingState =
    !isConnected &&
    !micError &&
    !callEnded &&
    (isStarting ||
      connectionState === 'connecting' ||
      agentState === 'connecting' ||
      agentState === 'initializing');

  return (
    <>
      <AnimatePresence mode="wait">
        {/* ── STATE 6: Microphone Permission Error Modal ── */}
        {micError && (
          <motion.div
            key="mic-error"
            {...VIEW_MOTION_PROPS}
            className="fixed inset-0 z-[100] mic-error-overlay flex items-center justify-center p-4"
          >
            <div className="glass-card bg-card/95 border border-red-500/20 rounded-3xl p-8 max-w-md w-full text-center shadow-2xl backdrop-blur-xl animate-float-in">
              {/* Crossed Mic Icon */}
              <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-red-500/10 text-red-500 border border-red-500/20 shadow-inner">
                <svg
                  width="36"
                  height="36"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="1" y1="1" x2="23" y2="23" />
                  <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6" />
                  <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2c0 .67-.08 1.32-.22 1.94" />
                  <line x1="12" y1="19" x2="12" y2="23" />
                  <line x1="8" y1="23" x2="16" y2="23" />
                </svg>
              </div>

              <h2 className="text-foreground text-2xl font-bold mb-2">
                Microphone access needed
              </h2>
              <p className="text-muted-foreground text-sm mb-6 leading-relaxed">
                Microphone access was blocked. Please enable microphone access in your browser settings to speak with Nova.
              </p>

              {/* How to enable instructions guide */}
              {showHowToEnable && (
                <div className="text-left bg-muted/60 border border-border/50 rounded-2xl p-4 mb-6 space-y-3 animate-float-in text-xs">
                  <p className="font-semibold text-foreground">
                    How to enable your microphone:
                  </p>
                  <div className="flex items-start gap-2.5 text-muted-foreground">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-500/20 text-blue-400 font-bold text-[10px]">
                      1
                    </span>
                    <span>Click the lock icon (🔒) in your browser address bar</span>
                  </div>
                  <div className="flex items-start gap-2.5 text-muted-foreground">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-500/20 text-blue-400 font-bold text-[10px]">
                      2
                    </span>
                    <span>Find <strong>Microphone</strong> and set permission to <strong>Allow</strong></span>
                  </div>
                  <div className="flex items-start gap-2.5 text-muted-foreground">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-500/20 text-blue-400 font-bold text-[10px]">
                      3
                    </span>
                    <span>Click <strong>Try Again</strong> below</span>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3">
                <Button
                  onClick={() => {
                    if (onRestartSession) {
                      onRestartSession();
                    } else {
                      handleStart();
                    }
                  }}
                  className="flex-1 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-semibold shadow-lg shadow-blue-500/25 py-5"
                >
                  Try Again
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowHowToEnable((prev) => !prev)}
                  className="flex-1 rounded-full border-border/80 text-foreground hover:bg-foreground/5 py-5"
                >
                  {showHowToEnable ? 'Hide steps' : 'How to enable'}
                </Button>
              </div>
            </div>
          </motion.div>
        )}

        {/* ── STATE 2: Connecting (The agent is joining the call; tell the user to wait) ── */}
        {isConnectingState && (
          <motion.div
            key="connecting"
            {...VIEW_MOTION_PROPS}
            className="flex min-h-svh flex-col items-center justify-center text-center px-6 py-20 relative"
          >
            {/* Background Glow */}
            <div className="hero-glow pointer-events-none absolute inset-0" />

            {/* Central Animated Loader */}
            <div className="relative my-8 flex items-center justify-center">
              <div className="animate-orb-glow absolute h-48 w-48 rounded-full bg-blue-500/20 blur-3xl" />
              <div className="animate-ring-pulse absolute h-40 w-40 rounded-full border-2 border-blue-400/40" />
              <div className="flex h-32 w-32 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 shadow-2xl shadow-blue-500/30">
                <span className="h-10 w-10 rounded-full border-4 border-white border-t-transparent animate-ln-spin" />
              </div>
            </div>

            {/* Connecting Badge */}
            <div className="flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-1.5 text-xs font-semibold text-blue-400 shadow-md mb-4">
              <span className="h-2 w-2 rounded-full bg-blue-400 animate-ping" />
              <span className="tracking-wide uppercase">Connecting</span>
            </div>

            <h2 className="text-foreground text-2xl font-bold md:text-3xl mb-2">
              Joining call...
            </h2>
            <p className="text-muted-foreground max-w-sm text-sm font-medium">
              The agent is joining the call; please wait...
            </p>
          </motion.div>
        )}

        {/* ── STATE 5: Call ended (The conversation is over; show an option to start again) ── */}
        {!isConnected && callEnded && !micError && !isConnectingState && (
          <motion.div
            key="call-ended"
            {...VIEW_MOTION_PROPS}
            className="flex min-h-svh flex-col items-center justify-center text-center px-6 py-20"
          >
            {/* End Call Icon */}
            <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-blue-500/10 border border-blue-500/20 shadow-xl animate-subtle-float">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" className="text-blue-400">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>

            <div className="flex items-center gap-2 rounded-full border border-border bg-muted/40 px-4 py-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">
              Call ended
            </div>

            <h2 className="text-foreground text-3xl font-bold tracking-tight md:text-4xl mb-3">
              Conversation Over
            </h2>
            <p className="text-muted-foreground max-w-sm text-base leading-relaxed mb-8">
              The conversation has ended. Start again whenever you are ready.
            </p>

            {/* Start Again Option Button */}
            <Button
              size="lg"
              onClick={() => {
                if (onRestartSession) {
                  onRestartSession();
                } else {
                  handleStart();
                }
              }}
              id="nova-restart-button"
              className="w-72 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 px-8 py-6 text-base font-bold text-white shadow-xl shadow-blue-500/25 hover:shadow-blue-500/40 hover:scale-[1.03] transition-all duration-300"
            >
              ↻ Start Again
            </Button>
          </motion.div>
        )}

        {/* ── STATE 1: Ready (The agent has not started yet; show one clear button to begin) ── */}
        {!isConnected && !callEnded && !micError && !isConnectingState && (
          <MotionWelcomeView
            key="welcome"
            {...VIEW_MOTION_PROPS}
            startButtonText={appConfig.startButtonText}
            onStartCall={handleStart}
            isStarting={isStarting}
          />
        )}

        {/* ── STATES 3 & 4: Active Session (Nova UI — always rendered when connected) ── */}
        {isConnected && (
          <MotionSessionView
            key="session-view"
            {...VIEW_MOTION_PROPS}
            messages={messages}
            supportsChatInput={appConfig.supportsChatInput}
            supportsVideoInput={appConfig.supportsVideoInput}
            supportsScreenShare={appConfig.supportsScreenShare}
            isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
            audioVisualizerType={appConfig.audioVisualizerType}
            audioVisualizerColor={
              resolvedTheme === 'dark'
                ? appConfig.audioVisualizerColorDark
                : appConfig.audioVisualizerColor
            }
            audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
            audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
            audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
            audioVisualizerGridColumnCount={
              appConfig.audioVisualizerGridColumnCount
            }
            audioVisualizerRadialBarCount={
              appConfig.audioVisualizerRadialBarCount
            }
            audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
            audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
            className="fixed inset-0"
            onDisconnect={handleEnd}
          />
        )}

        {/* ── Zenith Overlay — automatically appears when math specialist is active ── */}
        {isConnected && isZenithActive && (
          <ZenithOverlay
            key="zenith-overlay"
            messages={messages}
            supportsChatInput={appConfig.supportsChatInput}
            onDisconnect={handleEnd}
          />
        )}
      </AnimatePresence>
    </>
  );
}
