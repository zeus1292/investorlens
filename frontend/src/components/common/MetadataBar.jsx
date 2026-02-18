import { formatElapsed } from '../../utils/format';

export default function MetadataBar({ metadata, persona, resultCount }) {
  if (!metadata) return null;
  return (
    <div className="flex flex-wrap items-center gap-4 text-xs text-surface-500">
      {resultCount != null && <span>{resultCount} results</span>}
      {metadata.candidates_evaluated != null && (
        <span>{metadata.candidates_evaluated} candidates evaluated</span>
      )}
      {metadata.total_elapsed_ms != null && (
        <span>{formatElapsed(metadata.total_elapsed_ms)}</span>
      )}
      {persona && <span className="text-surface-600">{persona}</span>}
    </div>
  );
}
