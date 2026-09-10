import Card from '../common/Card';
import StatusBadge from '../common/StatusBadge';
import { Notice } from '../common/EmptyState';
import { pct } from '../../utils/format';

export default function FaceCard({ face }) {
  if (!face) return null;
  const tone =
    face.status === 'detected'
      ? 'ok'
      : face.status === 'multiple_detected'
      ? 'warn'
      : 'idle';

  return (
    <Card
      title="Face Detection"
      sub="Document photograph localization"
      right={<StatusBadge tone={tone}>{face.status}</StatusBadge>}
    >
      {face.status === 'unavailable' || face.status === 'not_detected' ? (
        <Notice tone="info">
          {face.message ||
            'No face detected on the document. The bounding box overlay appears on the preview when a face is found.'}
        </Notice>
      ) : (
        <>
          <div className="metrics">
            <div className="metric">
              <div className="m-label">Faces Found</div>
              <div className="m-value">{face.faces?.length ?? 0}</div>
            </div>
            {face.primary_face && (
              <div className="metric">
                <div className="m-label">Primary Box</div>
                <div className="m-value" style={{ fontSize: 13 }}>
                  {face.primary_face.width}×{face.primary_face.height}
                </div>
              </div>
            )}
          </div>
          <p className="disclaimer">
            Bounding box is overlaid on the document preview (left).
          </p>
        </>
      )}

      <div className="section-label" style={{ marginTop: 14, marginBottom: 6 }}>
        Traveller Comparison
      </div>
      {face.comparison_available ? (
        <div className="check">
          <span className="c-name">Similarity</span>
          <StatusBadge tone={face.match_status === 'match' ? 'ok' : 'err'}>
            {pct(face.similarity)} · {face.match_status}
          </StatusBadge>
        </div>
      ) : (
        <Notice tone="info">
          Face comparison is not available in this prototype build. No similarity
          score is fabricated.
        </Notice>
      )}
    </Card>
  );
}
