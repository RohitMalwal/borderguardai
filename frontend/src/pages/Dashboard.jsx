import Card from '../components/common/Card';
import StatusBadge from '../components/common/StatusBadge';
import { PIPELINE_STAGES, FUTURE_MODULES } from '../data/pipelineStages';

// Light landing / overview. The operational surface is the Screening page.
export default function Dashboard({ onOpenScreening }) {
  return (
    <div className="main-area" style={{ maxWidth: 900, margin: '0 auto' }}>
      <div className="overall-banner">
        <div>
          <div className="ob-title">Explainable border document screening</div>
          <div className="ob-sub">
            Local-first · offline-capable · no external AI services
          </div>
        </div>
        <button className="btn" style={{ width: 'auto' }} onClick={onOpenScreening}>
          Open Screening Console
        </button>
      </div>

      <Card title="Active Pipeline" sub="Implemented in this prototype">
        <div className="check-grid">
          {PIPELINE_STAGES.map((s) => (
            <div className="check" key={s.key}>
              <span className="c-name">{s.label}</span>
              <StatusBadge tone="ok">live</StatusBadge>
            </div>
          ))}
        </div>
      </Card>

      <div style={{ height: 16 }} />

      <Card title="Roadmap Modules" sub="Designed for — not yet implemented">
        <div className="check-grid">
          {FUTURE_MODULES.map((m) => (
            <div className="check" key={m}>
              <span className="c-name">{m}</span>
              <StatusBadge tone="idle">planned</StatusBadge>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
