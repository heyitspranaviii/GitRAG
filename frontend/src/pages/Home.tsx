import { useRef, useEffect } from 'react';
import { IngestPanel } from '../components/IngestPanel';
import { ChatMessage } from '../components/ChatMessage';
import { ChatInput } from '../components/ChatInput';
import { StatusBar } from '../components/StatusBar';
import { useHealth } from '../hooks/useHealth';
import { useAppStore } from '../store';

export function Home() {
  useHealth();
  const messages    = useAppStore((s) => s.messages);
  const isQuerying  = useAppStore((s) => s.isQuerying);
  const bottomRef   = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">GitRAG</h1>
          <p className="text-xs text-gray-400">Chat with any repository — locally</p>
        </div>
      </header>

      {/* Status bar */}
      <StatusBar />

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <aside className="w-80 border-r border-gray-200 bg-white flex flex-col p-4 gap-4 overflow-y-auto">
          <IngestPanel />

          <div className="text-xs text-gray-400 space-y-1 mt-2">
            <p className="font-medium text-gray-500 mb-2">Example questions</p>
            {[
              'How does authentication work?',
              'What happens when process_payment() is called?',
              'Is the login handler secure?',
              'Trace the request lifecycle',
              'Where are database queries made?',
            ].map((q) => (
              <p key={q} className="text-gray-400 text-xs leading-relaxed">· {q}</p>
            ))}
          </div>
        </aside>

        {/* Chat area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto px-6 py-4">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full text-center">
                <div>
                  <p className="text-gray-400 text-sm">No messages yet.</p>
                  <p className="text-gray-300 text-xs mt-1">Ingest a repository and ask your first question.</p>
                </div>
              </div>
            ) : (
              <>
                {messages.map((m) => <ChatMessage key={m.id} message={m} />)}
                {isQuerying && (
                  <div className="flex justify-start mb-4">
                    <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3">
                      <div className="flex gap-1">
                        {[0, 1, 2].map((i) => (
                          <div key={i} className="w-2 h-2 bg-gray-300 rounded-full animate-bounce"
                               style={{ animationDelay: `${i * 0.15}s` }} />
                        ))}
                      </div>
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </>
            )}
          </div>
          <ChatInput />
        </main>
      </div>
    </div>
  );
}
