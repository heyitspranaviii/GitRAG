import { useState } from 'react';
import { useIngest } from '../hooks/useIngest';
import { useAppStore } from '../store';

export function IngestPanel() {
  const [repoPath, setRepoPath] = useState('');
  const { ingest } = useIngest();
  const { isIngesting, ingestStats, error } = useAppStore();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    ingest(repoPath);
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
      <h2 className="text-sm font-semibold text-gray-700 mb-3">Ingest repository</h2>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={repoPath}
          onChange={(e) => setRepoPath(e.target.value)}
          placeholder="/absolute/path/to/repo  or  C:\repos\myproject"
          className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-900"
          disabled={isIngesting}
        />
        <button
          type="submit"
          disabled={isIngesting || !repoPath.trim()}
          className="px-4 py-2 text-sm bg-gray-900 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isIngesting ? 'Ingesting…' : 'Ingest'}
        </button>
      </form>

      {isIngesting && (
        <p className="mt-2 text-xs text-gray-500">
          Reading files, embedding chunks, building indexes… this takes a few minutes on CPU.
        </p>
      )}

      {ingestStats && !isIngesting && (
        <p className="mt-2 text-xs text-green-700">
          ✓ Done — {ingestStats.chunks.toLocaleString()} chunks from {ingestStats.files} files
          · {ingestStats.findings} security findings · {ingestStats.elapsed_s}s
        </p>
      )}

      {error && !isIngesting && (
        <p className="mt-2 text-xs text-red-600">✗ {error}</p>
      )}
    </div>
  );
}
