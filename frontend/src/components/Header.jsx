const STEPS = [
  { id: 'field', label: '1  Field' },
  { id: 'conditions', label: '2  Conditions' },
  { id: 'compare', label: '3  Compare' },
]

export default function Header({ page, setPage, hasData }) {
  return (
    <header className="header">
      <div className="container">
        <span className="logo" onClick={() => setPage('field')}>Field Shift</span>
        <nav className="steps">
          {STEPS.map((step, i) => (
            <span key={step.id}>
              {i > 0 && <span className="muted">—&nbsp;&nbsp;&nbsp;</span>}
              <button
                className={'step' + (page === step.id || (page === 'details' && step.id === 'compare') ? ' active' : '')}
                disabled={step.id !== 'field' && !hasData}
                onClick={() => setPage(step.id)}
              >
                {step.label}
              </button>
            </span>
          ))}
        </nav>
        <button className="link-button" onClick={() => setPage('how')}>How it works</button>
      </div>
    </header>
  )
}
