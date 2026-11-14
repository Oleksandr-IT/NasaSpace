import ScoreBars from '../components/ScoreBars'
import RotationCalendar from '../components/RotationCalendar'

export default function DetailsPage({ strategy, onBack }) {
  const { explanation } = strategy

  return (
    <>
      <button className="link-button" onClick={onBack}>← All options</button>
      <h1 style={{ margin: '16px 0 24px' }}>
        {strategy.is_current ? 'Current' : strategy.id} · {strategy.name}
      </h1>

      <div className="details-grid">
        <div className="card">
          <div className="section">
            <h2>Why we suggest it</h2>
            <p>{explanation.why}</p>
          </div>

          <div className="section">
            <h2>Evidence from your data</h2>
            {explanation.evidence.map((e) => (
              <div className="evidence-row" key={e.text}>
                <span>{e.text}</span>
                <span style={{ whiteSpace: 'nowrap' }}>
                  <span className="tag">{e.source}</span> <span className="tag">{e.confidence}</span>
                </span>
              </div>
            ))}
          </div>

          <div className="section">
            <h2>Possible benefits</h2>
            <ul>{explanation.benefits.map((b) => <li key={b}>{b}</li>)}</ul>
          </div>

          <div className="section">
            <h2>What we don't know</h2>
            <ul>{explanation.gaps.map((g) => <li key={g}>{g}</li>)}</ul>
          </div>

          <div className="section check-local">
            <h2>Check with a local expert</h2>
            <ul>{explanation.check_locally.map((c) => <li key={c}>{c}</li>)}</ul>
          </div>
        </div>

        <div className="card sticky">
          <div className="total-score">{strategy.total_score} <span>/ 100</span></div>
          <p className="small muted" style={{ marginBottom: 16 }}>Bare soil: about {strategy.bare_months_per_year} months a year</p>
          <ScoreBars scores={strategy.scores} />
          <div style={{ margin: '16px 0' }}>
            <RotationCalendar calendar={strategy.calendar} />
          </div>
          <button className="button secondary full" onClick={() => window.print()}>Print or save as PDF</button>
        </div>
      </div>
    </>
  )
}
