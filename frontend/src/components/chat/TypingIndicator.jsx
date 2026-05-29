export default function TypingIndicator({ names }) {
  if (!names || names.length === 0) return null;
  const text = names.length === 1 ? `${names[0]} печатает` : `${names.join(', ')} печатают`;
  return (
    <div className="typing-indicator">
      <div className="typing-dots">
        <span /><span /><span />
      </div>
      <span>{text}</span>
    </div>
  );
}
