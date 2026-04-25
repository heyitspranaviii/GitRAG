import { useState, useRef, type KeyboardEvent } from 'react';
import { useChat } from '../hooks/useChat';
import { useAppStore } from '../store';

export function ChatInput() {
  const [value, setValue]     = useState('');
  const textareaRef           = useRef<HTMLTextAreaElement>(null);
  const { sendMessage, clear } = useChat();
  const isQuerying             = useAppStore((s) => s.isQuerying);

  const submit = async () => {
    const q = value.trim();
    if (!q || isQuerying) return;
    setValue('');
    await sendMessage(q);
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white p-3">
      <div className="flex gap-2 items-end">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything about the codebase… (Enter to send, Shift+Enter for newline)"
          rows={2}
          disabled={isQuerying}
          className="flex-1 resize-none px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 disabled:opacity-50"
        />
        <div className="flex flex-col gap-1">
          <button
            onClick={submit}
            disabled={isQuerying || !value.trim()}
            className="px-4 py-2 text-sm bg-gray-900 text-white rounded-lg hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {isQuerying ? '…' : 'Send'}
          </button>
          <button
            onClick={clear}
            className="px-4 py-1 text-xs text-gray-400 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Clear
          </button>
        </div>
      </div>
      <p className="mt-1 text-xs text-gray-400">
        Try: "How does auth work?" · "What happens when login() is called?" · "Is the payment handler secure?"
      </p>
    </div>
  );
}
