// Canonical ordered pipeline stages shown in the UI. Keys mirror the backend
// PipelineStage enum so we can map stage timeline entries directly.
export const PIPELINE_STAGES = [
  { key: 'document', label: 'Document' },
  { key: 'quality', label: 'Quality' },
  { key: 'preprocessing', label: 'Preprocess' },
  { key: 'ocr', label: 'OCR' },
  { key: 'mrz', label: 'MRZ' },
  { key: 'validation', label: 'Validation' },
  { key: 'consistency', label: 'Consistency' },
  { key: 'face', label: 'Face' },
  { key: 'forensic', label: 'Forensic' },
];

// Future modules — displayed as locked/planned so the roadmap is legible
// without implying they run today.
export const FUTURE_MODULES = [
  'Watchlist Screening',
  'Risk Fusion',
  'RAG Evidence',
  'Explanation',
  'Officer Decision',
  'Offline Sync',
];
