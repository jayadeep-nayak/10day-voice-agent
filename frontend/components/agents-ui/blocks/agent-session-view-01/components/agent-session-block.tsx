'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Track } from 'livekit-client';
import { AnimatePresence, type MotionProps, motion } from 'motion/react';
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
import { Shimmer } from '@/components/ai-elements/shimmer';
import { cn } from '@/lib/shadcn/utils';
import { TileLayout } from './tile-view';

const MotionMessage = motion.create(Shimmer);

const BOTTOM_VIEW_MOTION_PROPS: MotionProps = {
  variants: {
    visible: {
      opacity: 1,
      translateY: '0%',
    },
    hidden: {
      opacity: 0,
      translateY: '100%',
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.3,
    delay: 0.2,
    ease: 'easeOut',
  },
};

const CHAT_MOTION_PROPS: MotionProps = {
  variants: {
    hidden: {
      opacity: 0,
      transition: {
        ease: 'easeOut',
        duration: 0.3,
      },
    },
    visible: {
      opacity: 1,
      transition: {
        delay: 0.2,
        ease: 'easeOut',
        duration: 0.3,
      },
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

const SHIMMER_MOTION_PROPS: MotionProps = {
  variants: {
    visible: {
      opacity: 1,
      transition: {
        ease: 'easeIn',
        duration: 0.5,
        delay: 0.8,
      },
    },
    hidden: {
      opacity: 0,
      transition: {
        ease: 'easeIn',
        duration: 0.5,
        delay: 0,
      },
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

interface FadeProps {
  top?: boolean;
  bottom?: boolean;
  className?: string;
}

export function Fade({ top = false, bottom = false, className }: FadeProps) {
  return (
    <div
      className={cn(
        'from-background pointer-events-none h-4 bg-linear-to-b to-transparent',
        top && 'bg-linear-to-b',
        bottom && 'bg-linear-to-t',
        className
      )}
    />
  );
}

export interface AgentSessionView_01Props {
  /**
   * Message shown above the controls before the first chat message is sent.
   *
   * @default "Go ahead, I'm listening..."
   */
  preConnectMessage?: string;
  /**
   * Enables or disables the chat toggle and transcript input controls.
   *
   * @default true
   */
  supportsChatInput?: boolean;
  /**
   * Enables or disables camera controls in the bottom control bar.
   *
   * @default false
   */
  supportsVideoInput?: boolean;
  /**
   * Enables or disables screen sharing controls in the bottom control bar.
   *
   * @default false
   */
  supportsScreenShare?: boolean;
  /**
   * Shows a pre-connect buffer state with a shimmer message before messages appear.
   *
   * @default true
   */
  isPreConnectBufferEnabled?: boolean;

  /** Selects the visualizer style rendered in the main tile area. */
  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  /** Primary hex color used by supported audio visualizer variants. */
  audioVisualizerColor?: `#${string}`;
  /** Hue shift intensity used by certain visualizers. */
  audioVisualizerColorShift?: number;
  /** Number of bars to render when `audioVisualizerType` is `bar`. */
  audioVisualizerBarCount?: number;
  /** Number of rows in the visualizer when `audioVisualizerType` is `grid`. */
  audioVisualizerGridRowCount?: number;
  /** Number of columns in the visualizer when `audioVisualizerType` is `grid`. */
  audioVisualizerGridColumnCount?: number;
  /** Number of radial bars when `audioVisualizerType` is `radial`. */
  audioVisualizerRadialBarCount?: number;
  /** Base radius of the radial visualizer when `audioVisualizerType` is `radial`. */
  audioVisualizerRadialRadius?: number;
  /** Stroke width of the wave path when `audioVisualizerType` is `wave`. */
  audioVisualizerWaveLineWidth?: number;
  /** Optional class name merged onto the outer `<section>` container. */
  className?: string;
  /** Callback when the user disconnects the session. */
  onDisconnect?: () => void;
}

export function AgentSessionView_01({
  preConnectMessage = "Go ahead, I'm listening...",
  supportsChatInput = true,
  supportsVideoInput = false,
  supportsScreenShare = false,
  isPreConnectBufferEnabled = true,

  audioVisualizerType,
  audioVisualizerColor,
  audioVisualizerColorShift,
  audioVisualizerBarCount,
  audioVisualizerGridRowCount,
  audioVisualizerGridColumnCount,
  audioVisualizerRadialBarCount,
  audioVisualizerRadialRadius,
  audioVisualizerWaveLineWidth,
  onDisconnect,
  ref,
  className,
  ...props
}: React.ComponentProps<'section'> & AgentSessionView_01Props) {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const [chatOpen, setChatOpen] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { state: agentState } = useAgent();
  const { localParticipant } = useLocalParticipant();

  // Call duration counter state
  const [callSeconds, setCallSeconds] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCallSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Check if user microphone is muted
  const micPublication = localParticipant.getTrackPublication(Track.Source.Microphone);
  const isMicMuted = !micPublication || micPublication.isMuted;

  const controls: AgentControlBarControls = {
    leave: true,
    microphone: true,
    chat: supportsChatInput,
    camera: false,
    screenShare: false,
  };

  useEffect(() => {
    const lastMessage = messages.at(-1);
    const lastMessageIsLocal = lastMessage?.from?.isLocal === true;

    if (scrollAreaRef.current && lastMessageIsLocal) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  // Voice Interaction State Map with interactive glowing badge styles
  const getVoiceStateInfo = () => {
    if (isMicMuted) {
      return {
        status: 'Microphone muted',
        subtitle: 'Your microphone is muted. Click the microphone button below to unmute.',
        badgeColor: 'glow-badge-muted text-red-400',
        dot: (
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-red-400">
            <line x1="1" y1="1" x2="23" y2="23" />
            <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6" />
          </svg>
        ),
      };
    }

    if (agentState === 'initializing' || agentState === 'connecting') {
      return {
        status: 'Connecting',
        subtitle: 'The agent is joining the call; please wait...',
        badgeColor: 'glow-badge-connecting text-cyan-400',
        dot: (
          <span className="h-2.5 w-2.5 rounded-full border-2 border-cyan-400 border-t-transparent animate-ln-spin" />
        ),
      };
    }
    if (agentState === 'speaking') {
      return {
        status: 'Nova is speaking',
        subtitle: 'Listen and follow along...',
        badgeColor: 'glow-badge-speaking text-blue-400',
        dot: (
          <span className="flex items-center gap-0.5">
            <span className="h-3 w-0.5 rounded-full bg-current animate-wave-bar-1" />
            <span className="h-4 w-0.5 rounded-full bg-current animate-wave-bar-2" />
            <span className="h-2.5 w-0.5 rounded-full bg-current animate-wave-bar-3" />
            <span className="h-3.5 w-0.5 rounded-full bg-current animate-wave-bar-4" />
            <span className="h-2.5 w-0.5 rounded-full bg-current animate-wave-bar-5" />
          </span>
        ),
      };
    }
    if (agentState === 'thinking') {
      return {
        status: 'Nova is thinking',
        subtitle: 'Processing speech...',
        badgeColor: 'border-purple-500/40 bg-purple-500/15 text-purple-400 shadow-lg shadow-purple-500/20',
        dot: (
          <span className="h-2.5 w-2.5 rounded-full border-2 border-purple-400 border-t-transparent animate-ln-spin" />
        ),
      };
    }
    // Default or Listening State
    return {
      status: 'Listening to you',
      subtitle: "Go ahead, I'm listening...",
      badgeColor: 'glow-badge-listening text-emerald-400',
      dot: <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-dot-pulse" />,
    };
  };

  const stateInfo = getVoiceStateInfo();

  const handleDisconnect = () => {
    session.end();
    onDisconnect?.();
  };

  return (
    <section
      ref={ref}
      className={cn(
        'bg-transparent relative z-10 h-full w-full overflow-hidden flex flex-col justify-between pt-20 pb-6',
        className
      )}
      {...props}
    >
      <Fade top className="absolute inset-x-4 top-0 z-10 h-40" />

      {/* ── Call Section Animated Background Energy Rings ── */}
      {!chatOpen && (
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center z-0">
          <div className="animate-call-ring-1 absolute h-[320px] w-[320px] rounded-full border border-blue-500/20 md:h-[480px] md:w-[480px]" />
          <div className="animate-call-ring-2 absolute h-[400px] w-[400px] rounded-full border border-cyan-400/15 md:h-[600px] md:w-[600px]" />
        </div>
      )}

      {/* ── Top Status Header: Live Timer + Interactive glowing badge + subtitle (z-40) ── */}
      <div className="relative z-40 flex flex-col items-center justify-center text-center px-4 pt-1 pointer-events-none">
        <AnimatePresence mode="wait">
          <motion.div
            key={stateInfo.status}
            initial={{ opacity: 0, y: -12, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.95 }}
            transition={{ duration: 0.35, ease: 'easeOut' }}
            className="flex flex-col items-center pointer-events-auto"
          >
            {/* Live Session Timer Pill */}
            <div className="mb-2 flex items-center gap-1.5 rounded-full border border-blue-500/20 bg-blue-500/10 px-3 py-0.5 text-[11px] font-mono font-semibold text-blue-300 backdrop-blur-md shadow-sm">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>LIVE SESSION</span>
              <span className="text-blue-400/60">•</span>
              <span>{formatTimer(callSeconds)}</span>
            </div>

            {/* Interactive Status Badge with Glass Glow */}
            <div
              className={cn(
                'flex items-center gap-2.5 rounded-full px-5 py-2 text-xs font-bold tracking-wider uppercase backdrop-blur-xl border transition-all duration-300 mb-1.5 hover:scale-[1.03]',
                stateInfo.badgeColor
              )}
            >
              {stateInfo.dot}
              <span>{stateInfo.status}</span>
            </div>

            {/* Subtitle Message */}
            <p className="text-muted-foreground/90 text-xs md:text-sm font-medium tracking-wide">
              {stateInfo.subtitle}
            </p>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Waveform / Audio Visualizer Area — Active mini visualizer in top-right when chat is open */}
      <TileLayout
        chatOpen={chatOpen}
        audioVisualizerType={audioVisualizerType}
        audioVisualizerColor={audioVisualizerColor}
        audioVisualizerColorShift={audioVisualizerColorShift}
        audioVisualizerBarCount={audioVisualizerBarCount}
        audioVisualizerRadialBarCount={audioVisualizerRadialBarCount}
        audioVisualizerRadialRadius={audioVisualizerRadialRadius}
        audioVisualizerGridRowCount={audioVisualizerGridRowCount}
        audioVisualizerGridColumnCount={audioVisualizerGridColumnCount}
        audioVisualizerWaveLineWidth={audioVisualizerWaveLineWidth}
      />

      {/* Transcript Area — Positioned cleanly starting below top status header */}
      <div className="absolute top-36 bottom-[140px] z-30 flex w-full flex-col pointer-events-auto">
        <AnimatePresence>
          {chatOpen && (
            <motion.div
              {...CHAT_MOTION_PROPS}
              className="flex h-full w-full flex-col gap-4 space-y-3 transition-opacity duration-300 ease-out"
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

      {/* ── Bottom Controls ── */}
      <motion.div
        {...BOTTOM_VIEW_MOTION_PROPS}
        className="relative z-50 mx-auto w-full max-w-lg px-4 flex flex-col gap-3"
      >
        {/* Pre-connect Buffer Shimmer Message */}
        {isPreConnectBufferEnabled && messages.length === 0 && !chatOpen && (
          <AnimatePresence>
            <MotionMessage
              key="pre-connect-message"
              duration={2}
              aria-hidden={messages.length > 0}
              {...SHIMMER_MOTION_PROPS}
              className="pointer-events-none mx-auto block w-full text-center text-xs font-semibold text-blue-400"
            >
              {preConnectMessage}
            </MotionMessage>
          </AnimatePresence>
        )}

        {/* Glassmorphism Control Bar with Glow */}
        <div className="glass-control-bar rounded-full p-2.5 transition-all duration-300 hover:border-blue-500/40">
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
    </section>
  );
}
