// API client for the BorderGuard backend.
//
// VITE_API_URL controls where API calls go. Leave it EMPTY in dev so requests
// are same-origin (/api ...) and Vite proxies them to the backend (see
// vite.config.js). Set it to a full origin (e.g. http://localhost:8000, or a
// LAN IP for a projector/demo machine) to point the built app at a backend
// directly. Never hard-code localhost in code — configure it here.

const BASE = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');

async function parseJsonSafe(res) {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

export async function getHealth() {
  const res = await fetch(`${BASE}/api/health`);
  if (!res.ok) throw new ApiError('Backend health check failed', res.status);
  return res.json();
}

export async function analyzeScreening({ passport, traveller }, { signal } = {}) {
  if (!passport) throw new ApiError('No document file provided', 0);

  const form = new FormData();
  form.append('passport', passport);
  if (traveller) form.append('traveller', traveller);

  let res;
  try {
    res = await fetch(`${BASE}/api/screening/analyze`, {
      method: 'POST',
      body: form,
      signal,
    });
  } catch (e) {
    if (e.name === 'AbortError') throw e;
    throw new ApiError(
      'Cannot reach the analysis backend. Make sure it is running and that '
        + 'VITE_API_URL points to it (default: http://localhost:8000).',
      0,
    );
  }

  const data = await parseJsonSafe(res);
  if (!res.ok) {
    const msg =
      (data && (data.message || data.detail)) ||
      'Analysis failed. Please try a clear image of the document biodata page.';
    throw new ApiError(msg, res.status, data && data.code);
  }
  return data;
}

export class ApiError extends Error {
  constructor(message, status, code) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}
