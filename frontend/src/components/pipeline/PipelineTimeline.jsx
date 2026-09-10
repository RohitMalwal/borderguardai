import { titleCase } from '../../utils/format';

// Horizontal stage strip. Reflects real backend stage statuses; while running,
// unreported stages animate as "processing" (never prematurely "complete").
export default function PipelineTimeline({ stages }) {
  return (
    <div className="pipeline">
      {stages.map((s) => (
        <div key={s.key} className={`stage ${s.status}`} title={s.message || ''}>
          <div className="st-name">{s.label}</div>
          <div className="st-status">{titleCase(s.status)}</div>
          <div className="st-bar">
            <i />
          </div>
        </div>
      ))}
    </div>
  );
}
