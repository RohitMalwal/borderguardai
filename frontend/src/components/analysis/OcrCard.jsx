import Card from '../common/Card';
import StatusBadge from '../common/StatusBadge';
import { Notice } from '../common/EmptyState';
import { fieldTone } from '../../utils/status';
import { pct, titleCase, orDash } from '../../utils/format';

const FIELD_ORDER = [
  'full_name',
  'surname',
  'given_names',
  'document_number',
  'nationality',
  'date_of_birth',
  'sex',
  'expiry_date',
];

export default function OcrCard({ ocr }) {
  if (!ocr) return null;
  const engineUnavailable = ocr.engine === 'unavailable';
  const tone = engineUnavailable
    ? 'idle'
    : ocr.status === 'complete'
    ? 'ok'
    : ocr.status === 'low_confidence'
    ? 'warn'
    : 'err';

  return (
    <Card
      title="Visual OCR"
      sub={`Engine: ${ocr.engine}${ocr.mean_confidence != null ? ` · mean conf ${pct(ocr.mean_confidence)}` : ''}`}
      right={<StatusBadge tone={tone}>{ocr.status}</StatusBadge>}
    >
      {engineUnavailable ? (
        <Notice tone="info">
          {ocr.message ||
            'The OCR engine is not available in this environment. No document text is fabricated.'}
        </Notice>
      ) : (
        <>
          {ocr.message && <Notice tone="warn">{ocr.message}</Notice>}
          <table className="data" style={{ marginTop: ocr.message ? 12 : 0 }}>
            <thead>
              <tr>
                <th>Field</th>
                <th>Value</th>
                <th>Confidence</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {FIELD_ORDER.map((key) => {
                const f = (ocr.fields || {})[key];
                if (!f) return null;
                return (
                  <tr key={key}>
                    <td className="muted">{titleCase(key)}</td>
                    <td className="val">{orDash(f.value)}</td>
                    <td className="muted">{f.confidence != null ? pct(f.confidence) : '—'}</td>
                    <td>
                      <StatusBadge tone={fieldTone(f.status)}>{f.status}</StatusBadge>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {ocr.raw_text?.length > 0 && (
            <details style={{ marginTop: 12 }}>
              <summary style={{ cursor: 'pointer', color: 'var(--accent)', fontSize: 12 }}>
                Raw detected text ({ocr.raw_text.length} lines)
              </summary>
              <div className="mrz-block" style={{ marginTop: 8, whiteSpace: 'pre-wrap', color: 'var(--text-1)' }}>
                {ocr.raw_text.map((l) => `${l.text}  ·  ${pct(l.confidence)}`).join('\n')}
              </div>
            </details>
          )}
        </>
      )}
    </Card>
  );
}
