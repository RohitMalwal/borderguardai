import Card from '../common/Card';
import StatusBadge from '../common/StatusBadge';
import { num } from '../../utils/format';

// Experimental signals only — explicitly NOT certified forensic analysis.
export default function ForensicCard({ forensic }) {
  if (!forensic) return null;
  const s = forensic.signals || {};

  return (
    <Card
      title="Forensic Signals"
      sub={forensic.label}
      right={<StatusBadge tone="warn">experimental</StatusBadge>}
    >
      {forensic.status === 'analyzed' ? (
        <div className="metrics">
          <Signal label="ELA Mean" value={num(s.ela_mean, 2)} />
          <Signal label="ELA Max" value={num(s.ela_max, 0)} />
          <Signal label="Noise σ" value={num(s.noise_std, 2)} />
          <Signal label="Edge Density" value={num(s.edge_density, 3)} />
        </div>
      ) : (
        <p className="muted">{forensic.message || 'Forensic signals unavailable.'}</p>
      )}
      <p className="disclaimer">{forensic.disclaimer}</p>
    </Card>
  );
}

function Signal({ label, value }) {
  return (
    <div className="metric">
      <div className="m-label">{label}</div>
      <div className="m-value">{value}</div>
    </div>
  );
}
