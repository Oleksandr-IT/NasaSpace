import { useState } from 'react'
import FieldMap from '../components/FieldMap'
import { DEMO_FIELDS } from '../demoFields'

const PRIORITIES = [
  { key: 'water', title: 'Save water', hint: 'Use less water across the rotation.' },
  { key: 'soil', title: 'Build soil health', hint: 'Keep soil productive for the long term.' },
  { key: 'erosion', title: 'Reduce erosion', hint: 'Keep topsoil in place after heavy rain.' },
  { key: 'income', title: 'Income from crops', hint: 'Favor crops with stronger earning potential.' },
]

const CONSTRAINTS = [
  { key: 'irrigation', title: 'I can irrigate' },
  { key: 'livestock', title: 'I have livestock (need forage)' },
  { key: 'small_grain_equipment', title: 'I have equipment for small grains' },
]

export default function FieldPage({ location, setLocation, priorities, setPriorities, constraints, setConstraints, onAnalyze, loading }) {
  const [coords, setCoords] = useState('')
  const [coordsError, setCoordsError] = useState('')

  // "42.10, -93.55" -> {lat, lon}
  function applyCoords() {
    const parts = coords.split(',').map((p) => parseFloat(p.trim()))
    const [lat, lon] = parts
    if (parts.length !== 2 || isNaN(lat) || isNaN(lon) || lat < 24 || lat > 50 || lon < -125 || lon > -66) {
      setCoordsError('Enter coordinates inside the continental US, for example: 42.10, -93.55')
      return
    }
    setCoordsError('')
    setLocation({ lat, lon })
  }

  const activeDemo = DEMO_FIELDS.find((d) => d.lat === location.lat && d.lon === location.lon)
  const label = `${location.lat.toFixed(2)}, ${location.lon.toFixed(2)}`

  return (
    <>
      <div className="page-title">
        <h1>Choose your field and priorities</h1>
        <p className="muted">Start with a location, then tell us what matters on your farm.</p>
      </div>

      <div className="grid-2">
        <div>
          <input
            className="input"
            placeholder="Paste coordinates, e.g. 42.10, -93.55 (press Enter)"
            value={coords}
            onChange={(e) => setCoords(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && applyCoords()}
          />
          {coordsError && <p className="error">{coordsError}</p>}
          <div className="chips">
            {DEMO_FIELDS.map((demo) => (
              <button
                key={demo.id}
                className={'chip' + (activeDemo?.id === demo.id ? ' active' : '')}
                onClick={() => setLocation({ lat: demo.lat, lon: demo.lon })}
              >
                {demo.label}
              </button>
            ))}
          </div>
          <div className="card map-card">
            <FieldMap
              lat={location.lat}
              lon={location.lon}
              label={label}
              onPick={(lat, lon) => setLocation({ lat: +lat.toFixed(2), lon: +lon.toFixed(2) })}
            />
          </div>
        </div>

        <div className="card">
          <h2>What matters most to you?</h2>
          <p className="card-subtitle">Choose 1 (less important) to 5 (most important).</p>

          {PRIORITIES.map((p) => (
            <div className="slider-row" key={p.key}>
              <div className="slider-head">
                <h3>{p.title}</h3>
                <span className="muted small">{priorities[p.key]} / 5</span>
              </div>
              <p className="small muted">{p.hint}</p>
              <input
                type="range" min="1" max="5" step="1"
                value={priorities[p.key]}
                onChange={(e) => setPriorities({ ...priorities, [p.key]: Number(e.target.value) })}
              />
            </div>
          ))}

          {CONSTRAINTS.map((c) => (
            <label className="toggle-row" key={c.key}>
              <span>{c.title}</span>
              <input
                type="checkbox"
                checked={constraints[c.key]}
                onChange={(e) => setConstraints({ ...constraints, [c.key]: e.target.checked })}
              />
            </label>
          ))}

          <button className="button full" style={{ marginTop: 16 }} onClick={onAnalyze} disabled={loading}>
            {loading ? 'Loading NASA and USDA data…' : 'Analyze this field'}
          </button>
          {loading && <p className="small muted" style={{ marginTop: 8 }}>A new field can take up to a minute the first time.</p>}
        </div>
      </div>
    </>
  )
}
