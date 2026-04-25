import { useCallback } from 'react';
import { queryRepo, clearMemory } from '../services/api';
import { useAppStore } from '../store';
import type { Message } from '../types';

function makeId() {
  return Math.random().toString(36).slice(2);
}

export function useChat() {
  const { sessionId, addMessage, clearMessages, setQuerying, setError, isQuerying } = useAppStore();

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isQuerying) return;
    setQuerying(true);
    setError(null);

    const userMsg: Message = {
      id: makeId(), role: 'user', content, timestamp: new Date(),
    };
    addMessage(userMsg);

    try {
      const data = await queryRepo(content, sessionId);
      const assistantMsg: Message = {
        id: makeId(), role: 'assistant', content: data.answer,
        timestamp: new Date(), elapsed_ms: data.elapsed_ms,
      };
      addMessage(assistantMsg);
    } catch (err: any) {
      const errMsg: Message = {
        id: makeId(), role: 'assistant',
        content: `**Error:** ${err.message}`,
        timestamp: new Date(),
      };
      addMessage(errMsg);
      setError(err.message);
    } finally {
      setQuerying(false);
    }
  }, [sessionId, addMessage, setQuerying, setError, isQuerying]);

  const clear = useCallback(async () => {
    await clearMemory(sessionId);
    clearMessages();
  }, [sessionId, clearMessages]);

  return { sendMessage, clear };
}
