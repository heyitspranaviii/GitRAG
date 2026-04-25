import { useAppStore } from '../store';

export function StatusBar() {
  const health = useAppStore((s) => s.health);

  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-gray-50 border-b border-gray-200 text-xs text-gray-500">
      <span className={`inline-block w-2 h-2 rounded-full ${health?.ready ? 'bg-green-500' : 'bg-amber-400'}`} />
      <span>{health?.ready ? `Ready · ${health.index_size.toLocaleString()} chunks indexed` : 'Not indexed — ingest a repo to begin'}</span>
      {health?.model && <span className="ml-auto font-mono text-gray-400">{health.model}</span>}
    </div>
  );
}
