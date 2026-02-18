export default function ErrorBanner({ message, onDismiss }) {
  if (!message) return null;
  return (
    <div className="flex items-center justify-between px-4 py-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
      <span>{message}</span>
      {onDismiss && (
        <button onClick={onDismiss} className="ml-4 text-red-400 hover:text-red-600 cursor-pointer">&times;</button>
      )}
    </div>
  );
}
