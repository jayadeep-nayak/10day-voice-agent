'use client';

/**
 * Nova state type — represents the visual state of the AI tutor.
 * Used across components to synchronize UI state with the LiveKit agent.
 */
export type NovaState =
  | 'idle'
  | 'connecting'
  | 'listening'
  | 'speaking'
  | 'thinking'
  | 'ended';
