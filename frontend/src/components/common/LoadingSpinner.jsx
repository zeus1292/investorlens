export default function LoadingSpinner({ message = 'Searching...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <div className="w-8 h-8 border-2 border-surface-600 border-t-persona-value rounded-full animate-spin" />
      <p className="text-surface-400 text-sm">{message}</p>
    </div>
  );
}
