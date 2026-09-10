export default function EmptyState({ title, children }) {
  return (
    <div className="empty">
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}

export function Notice({ tone = 'info', children }) {
  return <div className={`notice ${tone}`}>{children}</div>;
}
