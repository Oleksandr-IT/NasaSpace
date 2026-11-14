export const SCORE_LABELS = {
  water: 'Water use',
  soil_health: 'Soil health',
  erosion: 'Erosion control',
  pest_break: 'Pest break',
  income: 'Income',
  climate_risk: 'Weather resilience',
}

export default function ScoreBars({ scores }) {
  return (
    <div>
      {Object.entries(SCORE_LABELS).map(([key, label]) => (
        <div className="score-row" key={key}>
          <div className="score-head">
            <span>{label}</span>
            <span className="muted">{scores[key]}</span>
          </div>
          <div className="score-track">
            <div className="score-fill" style={{ width: `${scores[key]}%` }} />
          </div>
        </div>
      ))}
    </div>
  )
}
