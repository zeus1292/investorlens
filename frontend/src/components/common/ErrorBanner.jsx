export default function ErrorBanner({ message, onDismiss }) {
  if (!message) return null;
  return (
    <div className="flex items-center justify-between px-4 py-3 rounded-xl bg-red-900/30 border border-red-800 text-red-300 text-sm">
      <span>{message}</span>
      {onDismiss && (
        <button onClick={onDismiss} className="ml-4 text-red-400 hover:text-red-200 cursor-pointer">&times;</button>
      )}
    </div>
  );
}
