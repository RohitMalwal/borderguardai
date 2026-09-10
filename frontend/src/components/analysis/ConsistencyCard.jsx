import Card from '../common/Card';
import StatusBadge from '../common/StatusBadge';
import { Notice } from '../common/EmptyState';
import { fieldTone, overallConsistencyTone } from '../../utils/status';
import { titleCase, orDash } from '../../utils/format';

const FIELD_ORDER = [
  'full_name',
  'document_number',
  'nationality',
  'date_of_birth',
  'expiry_date',
  'sex',
];

// The core feature: field-by-field VISUAL OCR vs MRZ, with an explicit result
// per field (never a single opaque score).
export default function ConsistencyCard({ consistency }) {
  if (!consistency) return null;
  const tone = overallConsistencyTone(consistency.overall_status);

  return (
    <Card
      title="Cross-Validation · Visual OCR ↔ MRZ"
      sub={`${consistency.match_count}/${consistency.comparable_count} comparable fields matched`}
      right={<StatusBadge tone={tone}>{consistency.overall_status}</StatusBadge>}
    >
      {consistency.overall_status === 'not_available' ? (
        <Notice tone="info">
          Not enough data from OCR and MRZ to cross-validate. Both sources are
          required to compare identity fields.
        </Notice>
      ) : (
        <table className="data">
          <thead>
            <tr>
              <th>Field</th>
              <th>Visual OCR</th>
              <th>MRZ</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {FIELD_ORDER.map((key) => {
              const f = (consistency.fields || {})[key];
              if (!f) return null;
              return (
                <tr key={key}>
                  <td className="muted">{titleCase(key)}</td>
                  <td className="val">{orDash(f.visual)}</td>
                  <td className="val">{orDash(f.mrz)}</td>
                  <td title={f.detail || ''}>
                    <StatusBadge tone={fieldTone(f.status)}>{f.status}</StatusBadge>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
      {consistency.overall_status === 'mismatch' && (
        <Notice tone="err">
          Visual OCR and MRZ disagree on one or more identity fields. This
          warrants manual officer review.
        </Notice>
      )}
    </Card>
  );
}
