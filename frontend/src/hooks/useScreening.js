import { useCallback, useRef, useState } from 'react';
import { analyzeScreening } from '../api/client';
import { PIPELINE_STAGES } from '../data/pipelineStages';

// Owns the screening request lifecycle and derives per-stage UI status.
// While a request is in flight, stages animate as "processing" until the real
// backend result arrives — we never mark a stage complete before the server
// actually reports it.
export function useScreening() {
  const [status, setStatus] = useState('idle'); // idle | running | done | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);

  const run = useCallback(async (docFile, traveller) => {
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setStatus('running');
    setError(null);
    setResult(null);

    try {
      const data = await analyzeScreening(
        { passport: docFile, traveller },
        { signal: controller.signal },
      );
      setResult(data);
      setStatus('done');
    } catch (e) {
      if (e.name === 'AbortError') return;
      setError(e.message || 'Analysis failed.');
      setStatus('error');
    }
  }, []);

  const reset = useCallback(() => {
    if (abortRef.current) abortRef.current.abort();
    setStatus('idle');
    setResult(null);
    setError(null);
  }, []);

  // Build the ordered stage view. Backend returns a `stages` timeline; before
  // results we show pending, and during the run we show processing.
  const stageStates = deriveStages(status, result);

  return { status, result, error, run, reset, stageStates };
}

function deriveStages(status, result) {
  const byKey = {};
  if (result && Array.isArray(result.stages)) {
    for (const s of result.stages) byKey[s.stage] = s;
  }
  return PIPELINE_STAGES.map((stage) => {
    const entry = byKey[stage.key];
    if (entry) {
      return { ...stage, status: entry.status, message: entry.message };
    }
    if (status === 'running') return { ...stage, status: 'processing' };
    return { ...stage, status: 'pending' };
  });
}
