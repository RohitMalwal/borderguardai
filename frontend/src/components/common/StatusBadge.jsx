import { titleCase } from '../../utils/format';

// Small pill showing a status with a tone color. `label` overrides the text.
export default function StatusBadge({ tone = 'idle', label, children }) {
  const text = label ?? children ?? '';
  return (
    <span className={`badge ${tone}`}>
      <span className="b-dot" />
      {typeof text === 'string' ? titleCase(text) : text}
    </span>
  );
}
