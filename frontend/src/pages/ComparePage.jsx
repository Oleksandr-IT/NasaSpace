import ScoreBars from '../components/ScoreBars'
import RotationCalendar from '../components/RotationCalendar'

export default function ComparePage({ strategies, field, scenario, onScenario, onOpen }) {
  const dryYear = field.climate.year_types.dry[0]
  const scenarios = [
    { id: 'normal', label: 'Typical year' },
    { id: 'dry', label: `Dry year (like ${dryYear})` },
    { id: 'wet', label: 'Wet year' },
  ]

  return (
    <>
      <div className="page-title">
        <h1>{strategies.length} rotation options for your field</h1>
        <div className="segmented" style={{ marginTop: 8 }}>
          {scenarios.map((s) => (
            <button key={s.id} className={scenario === s.id ? 'active' : ''} onClick={() => onScenario(s.id)}>
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid-4">
        {strategies.map((s) => (
          <div className={'card option-card' + (s.best_match ? ' best' : '')} key={s.id}>
            <div>
              {s.is_current ? <span className="tag">Current</span> : <span className="tag">Option {s.id}</span>}{' '}
              {s.best_match && <span className="tag green">Best match for your priorities</span>}
              <h3 style={{ marginTop: 8 }}>{s.name}</h3>
            </div>
            <div className="total-score">{s.total_score} <span>/ 100</span></div>
            <ScoreBars scores={s.scores} />
            <RotationCalendar calendar={s.calendar} />
            <button className="link-button" style={{ textAlign: 'left', marginTop: 'auto' }} onClick={() => onOpen(s.id)}>
              Why this option →
            </button>
          </div>
        ))}
      </div>
    </>
  )
}
