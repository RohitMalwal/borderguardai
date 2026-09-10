import Card from '../common/Card';
import StatusBadge from '../common/StatusBadge';
import { Notice } from '../common/EmptyState';
import { mrzTone, checkTone } from '../../utils/status';
import { titleCase, orDash } from '../../utils/format';

const FIELD_ORDER = [
  'full_name',
  'document_number',
  'nationality',
  'date_of_birth',
  'sex',
  'expiry_date',
  'issuing_country',
  'document_type',
];

const CHECKS = [
  ['document_number', 'Document No.'],
  ['date_of_birth', 'Date of Birth'],
  ['expiry_date', 'Expiry Date'],
  ['composite', 'Composite'],
  ['line_lengths_ok', 'Line Lengths'],
];

export default function MrzCard({ mrz }) {
  if (!mrz) return null;

  if (!mrz.detected) {
    return (
      <Card title="Machine Readable Zone (MRZ)" right={<StatusBadge tone="idle">not detected</StatusBadge>}>
        <Notice tone="warn">
          {mrz.message ||
            'MRZ could not be reliably detected. Ensure the full biodata page, including the two bottom code lines, is visible.'}
        </Notice>
      </Card>
    );
  }

  return (
    <Card
      title="Machine Readable Zone (MRZ)"
      sub="ICAO TD3 · parsed and check-digit validated"
      right={<StatusBadge tone={mrzTone(mrz.status)}>{mrz.status}</StatusBadge>}
    >
      {mrz.raw_lines?.length > 0 && (
        <div className="mrz-block">{mrz.raw_lines.join('\n')}</div>
      )}

      <table className="data" style={{ marginTop: 14 }}>
        <thead>
          <tr>
            <th>Field</th>
            <th>Parsed Value</th>
          </tr>
        </thead>
        <tbody>
          {FIELD_ORDER.map((key) => (
            <tr key={key}>
              <td className="muted">{titleCase(key)}</td>
              <td className="val">{orDash((mrz.fields || {})[key])}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="section-label" style={{ marginTop: 16, marginBottom: 8 }}>
        Check-Digit Validation
      </div>
      <div className="check-grid">
        {CHECKS.map(([key, label]) => {
          const v = (mrz.validation || {})[key];
          const tone = checkTone(v);
          return (
            <div className="check" key={key}>
              <span className="c-name">{label}</span>
              <StatusBadge tone={tone}>
                {v === true ? 'pass' : v === false ? 'fail' : 'n/a'}
              </StatusBadge>
            </div>
          );
        })}
      </div>

      {mrz.errors?.length > 0 && (
        <Notice tone="err">
          <div>
            {mrz.errors.map((e, i) => (
              <div key={i}>• {e}</div>
            ))}
          </div>
        </Notice>
      )}
    </Card>
  );
}
