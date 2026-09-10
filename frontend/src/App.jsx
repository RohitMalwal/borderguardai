import { useState } from 'react';
import Header from './components/layout/Header';
import Screening from './pages/Screening';

// Two-phase flow: upload landing → analysis results.
// No nav tabs — the user sees only what's relevant to their current step.
export default function App() {
  const [phase, setPhase] = useState('upload'); // 'upload' | 'analysis'

  return (
    <div className="app">
      <Header />
      <Screening phase={phase} onPhaseChange={setPhase} />
    </div>
  );
}
