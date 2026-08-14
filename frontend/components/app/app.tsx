'use client';
import React, { useCallback, useMemo, useState } from 'react';
import { Room, TokenSource } from 'livekit-client';
import { useSession } from '@livekit/components-react';
import { WarningIcon } from '@phosphor-icons/react/dist/ssr';
import type { AppConfig } from '@/app-config';
import { AgentSessionProvider } from '@/components/agents-ui/agent-session-provider';
import { StartAudioButton } from '@/components/agents-ui/start-audio-button';
import { ViewController } from '@/components/app/view-controller';
import { Toaster } from '@/components/ui/sonner';
import { useAgentErrors } from '@/hooks/useAgentErrors';
import { useDebugMode } from '@/hooks/useDebug';
import { getSandboxTokenSource } from '@/lib/utils';

// Defensive patch to prevent duplicate text/byte stream handler registration crashes
if (typeof window !== 'undefined') {
  const originalRegisterText = Room.prototype.registerTextStreamHandler;
  if (originalRegisterText && !(originalRegisterText as unknown as { __patched?: boolean }).__patched) {
    const patchedRegisterText = function (this: Room, topic: string, callback: any) {
      try {
        this.unregisterTextStreamHandler(topic);
      } catch {
        // ignore
      }
      try {
        return originalRegisterText.call(this, topic, callback);
      } catch (err: any) {
        if (err?.message?.includes('already been set')) {
          return;
        }
        throw err;
      }
    };
    (patchedRegisterText as unknown as { __patched?: boolean }).__patched = true;
    Room.prototype.registerTextStreamHandler = patchedRegisterText;
  }

  const originalRegisterByte = Room.prototype.registerByteStreamHandler;
  if (originalRegisterByte && !(originalRegisterByte as unknown as { __patched?: boolean }).__patched) {
    const patchedRegisterByte = function (this: Room, topic: string, callback: any) {
      try {
        this.unregisterByteStreamHandler(topic);
      } catch {
        // ignore
      }
      try {
        return originalRegisterByte.call(this, topic, callback);
      } catch (err: any) {
        if (err?.message?.includes('already been set')) {
          return;
        }
        throw err;
      }
    };
    (patchedRegisterByte as unknown as { __patched?: boolean }).__patched = true;
    Room.prototype.registerByteStreamHandler = patchedRegisterByte;
  }
}

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';

function AppSetup() {
  useDebugMode({ enabled: IN_DEVELOPMENT });
  useAgentErrors();

  return null;
}

interface SessionContainerProps {
  appConfig: AppConfig;
  onRestart: () => void;
  autoStart?: boolean;
}

function SessionContainer({ appConfig, onRestart, autoStart = false }: SessionContainerProps) {
  const tokenSource = useMemo(() => {
    if (typeof process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT === 'string') {
      return getSandboxTokenSource(appConfig);
    }
    return TokenSource.custom(async () => {
      let userId = localStorage.getItem('voice_agent_user_id');
      if (!userId) {
        userId = 'usr_' + Math.random().toString(36).substring(2, 11);
        localStorage.setItem('voice_agent_user_id', userId);
      }
      localStorage.removeItem('voice_agent_user_name');
      const name = 'user';

      const res = await fetch(`/api/token?userId=${encodeURIComponent(userId)}&name=${encodeURIComponent(name)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId,
          name,
        }),
      });

      if (!res.ok) {
        throw new Error('Failed to fetch connection details');
      }

      return await res.json();
    });
  }, [appConfig]);

  const session = useSession(
    tokenSource,
    appConfig.agentName ? { agentName: appConfig.agentName } : undefined
  );

  return (
    <AgentSessionProvider session={session}>
      <AppSetup />
      <main className="grid h-svh grid-cols-1 place-content-center">
        <ViewController
          appConfig={appConfig}
          onRestartSession={onRestart}
          autoStart={autoStart}
        />
      </main>
      <StartAudioButton label="Start Audio" />
      <Toaster
        icons={{
          warning: <WarningIcon weight="bold" />,
        }}
        position="top-center"
        className="toaster group"
        style={
          {
            '--normal-bg': 'var(--popover)',
            '--normal-text': 'var(--popover-foreground)',
            '--normal-border': 'var(--border)',
          } as React.CSSProperties
        }
      />
    </AgentSessionProvider>
  );
}

interface AppProps {
  appConfig: AppConfig;
}

export function App({ appConfig }: AppProps) {
  const [currentKey, setCurrentKey] = useState(0);
  const [autoStartNext, setAutoStartNext] = useState(false);

  const handleRestart = useCallback(() => {
    setAutoStartNext(true);
    setCurrentKey((prev) => prev + 1);
  }, []);

  return (
    <SessionContainer
      key={currentKey}
      appConfig={appConfig}
      onRestart={handleRestart}
      autoStart={autoStartNext}
    />
  );
}
