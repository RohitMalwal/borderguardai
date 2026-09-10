import { useRef, useState } from 'react';
import DocumentPreview from './DocumentPreview';
import { bytesToSize } from '../../utils/format';

const ACCEPT = '.jpg,.jpeg,.png,image/jpeg,image/png';

// Upload panel: document (required) + optional traveller image, RUN button.
export default function UploadPanel({
  document,
  traveller,
  onDocument,
  onTraveller,
  onRun,
  onReset,
  running,
  facePrimary,
}) {
  return (
    <div>
      <div className="section-label">Document</div>
      <FileDrop
        file={document}
        onFile={onDocument}
        label="Drop document image here"
        hint="JPG, JPEG or PNG — the page with the photo and MRZ"
      />
      {document && (
        <DocumentPreview file={document} facePrimary={facePrimary} />
      )}
      {document && <FileMeta file={document} />}

      <div style={{ height: 18 }} />
      <div className="section-label">Traveller Photo · Optional</div>
      <FileDrop
        file={traveller}
        onFile={onTraveller}
        label="Drop live traveller photo"
        hint="Optional — enables face comparison when a matcher is available"
        compact
      />
      {traveller && <FileMeta file={traveller} />}

      <div className="btn-row">
        <button className="btn" disabled={!document || running} onClick={onRun}>
          {running ? (
            <>
              <span className="spinner" /> Analyzing…
            </>
          ) : (
            <>Run Screening</>
          )}
        </button>
      </div>
      {document && !running && (
        <button className="link-btn" style={{ marginTop: 10 }} onClick={onReset}>
          Clear and start over
        </button>
      )}
    </div>
  );
}

function FileDrop({ file, onFile, label, hint, compact }) {
  const inputRef = useRef(null);
  const [drag, setDrag] = useState(false);

  const pick = (f) => {
    if (f) onFile(f);
  };

  return (
    <div
      className={`dropzone ${drag ? 'drag' : ''}`}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDrag(true);
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDrag(false);
        pick(e.dataTransfer.files?.[0]);
      }}
      style={compact ? { padding: '16px 12px' } : undefined}
    >
      {!compact && (
        <div className="icon">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M12 16V4m0 0 4 4m-4-4-4 4" />
            <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
          </svg>
        </div>
      )}
      <div>{file ? file.name : label}</div>
      <div className="hint">{file ? 'Click to replace' : hint}</div>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        hidden
        onChange={(e) => pick(e.target.files?.[0])}
      />
    </div>
  );
}

function FileMeta({ file }) {
  return (
    <dl className="filemeta">
      <dt>File</dt>
      <dd>{file.name}</dd>
      <dt>Type</dt>
      <dd>{file.type || 'unknown'}</dd>
      <dt>Size</dt>
      <dd>{bytesToSize(file.size)}</dd>
    </dl>
  );
}
