import { useState } from 'react';
import UploadPanel from '../components/document/UploadPanel';
import PipelineTimeline from '../components/pipeline/PipelineTimeline';
import QualityCard from '../components/analysis/QualityCard';
import OcrCard from '../components/analysis/OcrCard';
import MrzCard from '../components/analysis/MrzCard';
import ConsistencyCard from '../components/analysis/ConsistencyCard';
import FaceCard from '../components/analysis/FaceCard';
import ForensicCard from '../components/analysis/ForensicCard';
import Card from '../components/common/Card';
import StatusBadge from '../components/common/StatusBadge';
import EmptyState, { Notice } from '../components/common/EmptyState';
import { useScreening } from '../hooks/useScreening';
import { overallConsistencyTone } from '../utils/status';
import { FUTURE_MODULES } from '../data/pipelineStages';

export default function Screening({ phase, onPhaseChange }) {
  const [document, setDocument] = useState(null);
  const [traveller, setTraveller] = useState(null);
  const { status, result, error, run, reset, stageStates } = useScreening();

  const running = status === 'running';
  const face = result?.face;

  const handleRun = () => {
    onPhaseChange('analysis');
    run(document, traveller);
  };

  const handleReset = () => {
    setDocument(null);
    setTraveller(null);
    reset();
    onPhaseChange('upload');
  };

  // ── Phase 1: Upload landing ──────────────────────────────────────────────
  if (phase === 'upload') {
    return (
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '48px 24px 80px',
          gap: 32,
        }}
      >
        {/* Hero heading */}
        <div style={{ textAlign: 'center', maxWidth: 520 }}>
          <h1
            style={{
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: '-0.02em',
              marginBottom: 10,
              color: 'var(--text-0)',
            }}
          >
            Document Screening
          </h1>
          <p style={{ color: 'var(--text-1)', fontSize: 15, lineHeight: 1.6 }}>
            Upload a document to begin AI-powered analysis — OCR, MRZ
            validation, face detection and cross-field consistency checks.
          </p>
        </div>

        {/* Upload card */}
        <div
          style={{
            width: '100%',
            maxWidth: 460,
            background: 'var(--bg-1)',
            border: '1px solid var(--line)',
            borderRadius: 'var(--radius)',
            padding: '28px 28px 24px',
            boxShadow: 'var(--shadow)',
          }}
        >
          <UploadPanel
            document={document}
            traveller={traveller}
            onDocument={setDocument}
            onTraveller={setTraveller}
            onRun={handleRun}
            onReset={handleReset}
            running={running}
            facePrimary={face?.primary_face}
          />
        </div>

        <p
          style={{
            fontSize: 11,
            color: 'var(--text-2)',
            textAlign: 'center',
            maxWidth: 400,
            lineHeight: 1.6,
            fontStyle: 'italic',
          }}
        >
          All processing runs locally. This prototype does not access any
          government database and does not provide certified forensic analysis.
        </p>
      </div>
    );
  }

  // ── Phase 2: Analysis view ───────────────────────────────────────────────
  return (
    <div className="workspace">
      <aside className="left-rail">
        <UploadPanel
          document={document}
          traveller={traveller}
          onDocument={setDocument}
          onTraveller={setTraveller}
          onRun={handleRun}
          onReset={handleReset}
          running={running}
          facePrimary={face?.primary_face}
        />

        <div className="footer-note">
          BorderGuard AI independently analyzes the document's{' '}
          <b>visual data</b> and its <b>machine-readable zone</b>, then
          cross-checks them to surface inconsistencies. All processing runs
          locally. This prototype does not access any government database and
          does not provide certified forensic analysis.
        </div>
      </aside>

      <main className="main-area">
        <Card title="Screening Pipeline" sub="Stages reflect real backend processing">
          <PipelineTimeline stages={stageStates} />
        </Card>

        <div style={{ height: 18 }} />

        {status === 'error' && <Notice tone="err">{error}</Notice>}

        {running && (
          <EmptyState title="Analyzing document…">
            Running local processing. Results appear here as soon as the backend
            returns — stages will not show complete until they actually are.
          </EmptyState>
        )}

        {status === 'done' && result && (
          <>
            <OverallBanner result={result} />
            {result.warnings?.length > 0 && (
              <Notice tone="warn">
                <div>
                  {result.warnings.slice(0, 3).map((w, i) => (
                    <div key={i}>• {w}</div>
                  ))}
                </div>
              </Notice>
            )}
            <div style={{ height: 16 }} />
            <ConsistencyCard consistency={result.consistency} />
            <div className="grid-2" style={{ marginTop: 16 }}>
              <div>
                <MrzCard mrz={result.mrz} />
              </div>
              <div>
                <OcrCard ocr={result.visual_ocr} />
              </div>
            </div>
            <div className="grid-2" style={{ marginTop: 16 }}>
              <div>
                <QualityCard quality={result.quality} />
              </div>
              <div>
                <FaceCard face={result.face} />
              </div>
            </div>
            <div style={{ marginTop: 16 }}>
              <ForensicCard forensic={result.forensic} />
            </div>
            <FutureModules />
          </>
        )}
      </main>
    </div>
  );
}

function OverallBanner({ result }) {
  const c = result.consistency;
  const tone = c ? overallConsistencyTone(c.overall_status) : 'idle';
  const headline =
    c?.overall_status === 'match'
      ? 'Visual and machine-readable data are consistent'
      : c?.overall_status === 'mismatch'
      ? 'Inconsistencies detected — manual review recommended'
      : c?.overall_status === 'partial'
      ? 'Partial consistency — some fields need review'
      : 'Analysis complete';

  return (
    <div className="overall-banner">
      <div>
        <div className="ob-title">{headline}</div>
        <div className="ob-sub">
          Screening {result.screening_id} · schema v{result.schema_version}
        </div>
      </div>
      <StatusBadge tone={tone}>{c?.overall_status || result.status}</StatusBadge>
    </div>
  );
}

function FutureModules() {
  return (
    <Card title="Downstream Modules" sub="Planned — not active in this prototype">
      <div className="check-grid">
        {FUTURE_MODULES.map((m) => (
          <div className="check" key={m}>
            <span className="c-name">{m}</span>
            <StatusBadge tone="idle">planned</StatusBadge>
          </div>
        ))}
      </div>
      <p className="disclaimer">
        These stages consume the same structured result contract and will be
        wired in without changing the document-analysis pipeline.
      </p>
    </Card>
  );
}
