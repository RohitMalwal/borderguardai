import Card from '../common/Card';
import StatusBadge from '../common/StatusBadge';
import { Notice } from '../common/EmptyState';
import { qualityTone } from '../../utils/status';
import { num } from '../../utils/format';

const toneColor = { ok: 'var(--ok)', warn: 'var(--warn)', err: 'var(--err)' };

export default function QualityCard({ quality }) {
  if (!quality) return null;
  const tone = qualityTone(quality.status);
  const res = quality.resolution || {};

  return (
    <Card
      title="Image Quality"
      sub="Computed from the uploaded image (OpenCV)"
      right={<StatusBadge tone={tone}>{quality.status}</StatusBadge>}
    >
      <div className="metrics">
        <Metric label="Quality" value={num(quality.quality_score, 0)} unit="/100" bar={quality.quality_score} tone={tone} />
        <Metric label="Sharpness" value={num(quality.blur_score, 0)} unit="var" />
        <Metric label="Brightness" value={num(quality.brightness_score, 0)} unit="/255" />
        <Metric label="Contrast" value={num(quality.contrast_score, 0)} unit="σ" />
        <Metric label="Resolution" value={`${res.width || '—'}×${res.height || '—'}`} unit={`${res.megapixels ?? '—'}MP`} />
      </div>
      {(quality.warnings || []).map((w, i) => (
        <Notice key={i} tone="warn">{w}</Notice>
      ))}
    </Card>
  );
}

function Metric({ label, value, unit, bar, tone }) {
  return (
    <div className="metric">
      <div className="m-label">{label}</div>
      <div className="m-value">
        {value}
        {unit && <span className="m-unit">{unit}</span>}
      </div>
      {bar !== undefined && (
        <div className="meter">
          <i style={{ width: `${Math.max(0, Math.min(100, bar))}%`, background: toneColor[tone] }} />
        </div>
      )}
    </div>
  );
}
