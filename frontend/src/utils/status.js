// Map backend status strings to a UI tone (ok | warn | err | idle).

export function stageTone(status) {
  switch (status) {
    case 'complete':
      return 'ok';
    case 'processing':
      return 'idle';
    case 'warning':
      return 'warn';
    case 'error':
      return 'err';
    case 'skipped':
    case 'pending':
    default:
      return 'idle';
  }
}

export function fieldTone(status) {
  switch (status) {
    case 'match':
    case 'valid':
    case 'detected':
      return 'ok';
    case 'low_confidence':
    case 'partial':
      return 'warn';
    case 'mismatch':
    case 'invalid':
      return 'err';
    case 'not_available':
    case 'not_detected':
    default:
      return 'idle';
  }
}

export function mrzTone(status) {
  switch (status) {
    case 'valid':
    case 'detected':
      return 'ok';
    case 'low_confidence':
      return 'warn';
    case 'invalid':
      return 'err';
    case 'not_detected':
    default:
      return 'idle';
  }
}

export function qualityTone(status) {
  return status === 'good' ? 'ok' : status === 'acceptable' ? 'warn' : 'err';
}

export function overallConsistencyTone(status) {
  return { match: 'ok', partial: 'warn', mismatch: 'err' }[status] || 'idle';
}

// Boolean check-digit -> tone. null means "not applicable".
export function checkTone(value) {
  if (value === true) return 'ok';
  if (value === false) return 'err';
  return 'idle';
}
