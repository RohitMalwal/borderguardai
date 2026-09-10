import { useEffect, useState } from 'react';
import { getHealth } from '../../api/client';

// Top bar with brand and live backend capability indicators.
export default function Header() {
  const [health, setHealth] = useState(null);
  const [online, setOnline] = useState(null);

  useEffect(() => {
    let alive = true;
    getHealth()
      .then((h) => alive && (setHealth(h), setOnline(true)))
      .catch(() => alive && setOnline(false));
    return () => {
      alive = false;
    };
  }, []);

  const caps = health?.capabilities || {};

  return (
    <header className="header">
      <div className="brand">
        <div className="brand-mark">
          <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2">
            <path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3Z" />
            <path d="M9 12l2 2 4-4" stroke="#e0f0ff" />
          </svg>
        </div>
        <div>
          <div className="brand-title">BorderGuard AI</div>
          <div className="brand-sub">Document Screening Console</div>
        </div>
      </div>

      <div className="header-status">
        <span className="cap-pill">
          <span className={`dot ${online ? 'on' : online === false ? 'off' : ''}`} />
          {online === null ? 'Connecting…' : online ? 'Backend online' : 'Backend offline'}
        </span>
        <Cap label="OCR" on={caps.ocr} />
        <Cap label="MRZ" on={caps.mrz_validation} />
        <Cap label="Face" on={caps.face_detection} />
      </div>
    </header>
  );
}

function Cap({ label, on }) {
  return (
    <span className="cap-pill" title={on ? `${label} available` : `${label} unavailable`}>
      <span className={`dot ${on ? 'on' : 'off'}`} />
      {label}
    </span>
  );
}
