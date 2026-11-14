import { useEffect, useState } from 'react'
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { getSatellite } from '../api'

// Порівнюємо модель (NASA POWER) із супутниками (GPM IMERG, SMAP).
// Челендж прямо просить пояснити, чим супутникові дані відрізняються від інших.
export default function SatelliteCard({ lat, lon, powerRain }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    setData(null)
    setError(null)
    getSatellite(lat, lon).then(setData).catch((e) => setError(e.message))
  }, [lat, lon])

  if (error) {
    return (
      <div className="card">
        <h2>Satellite check</h2>
        <p className="muted small">NASA satellite data is not available right now ({error}).</p>
      </div>
    )
  }
  if (!data) {
    return (
      <div className="card">
        <h2>Satellite check</h2>
        <p className="muted">Loading NASA IMERG and SMAP data… A new field can take about 2 minutes.</p>
      </div>
    )
  }

  // Одна таблиця за роками: опади з моделі POWER і з супутника IMERG
  const imerg = Object.fromEntries(data.imerg_season_rain.map((r) => [r.year, r.value]))
  const rainRows = powerRain.filter((r) => imerg[r.year] !== undefined)
    .map((r) => ({ year: r.year, power: r.value, imerg: imerg[r.year] }))
  const meanOf = (key) => rainRows.reduce((sum, r) => sum + r[key], 0) / rainRows.length
  const difference = Math.round(((meanOf('imerg') - meanOf('power')) / meanOf('power')) * 100)

  return (
    <div className="card">
      <h2>Satellite check</h2>
      <p className="card-subtitle">
        Model data (NASA POWER) compared with satellite measurements (NASA GPM IMERG and SMAP).
      </p>
      <div className="grid-2-equal">
        <div>
          <h3>May–Sep rainfall, mm</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={rainRows} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke="#e2ded5" />
              <XAxis dataKey="year" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line dataKey="power" name="NASA POWER (model)" stroke="#1f2421" dot={false} />
              <Line dataKey="imerg" name="GPM IMERG (satellite)" stroke="#2f6690" dot={false} />
            </LineChart>
          </ResponsiveContainer>
          <p className="small">
            On average the satellite shows {Math.abs(difference)}% {difference >= 0 ? 'more' : 'less'} summer rain than the model.
          </p>
        </div>
        <div>
          <h3>Root-zone soil moisture, m³/m³</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={data.smap_season_soil} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke="#e2ded5" />
              <XAxis dataKey="year" tick={{ fontSize: 12 }} />
              <YAxis domain={['auto', 'auto']} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Line dataKey="value" name="SMAP L4, May–Sep" stroke="#3f6b3a" dot />
            </LineChart>
          </ResponsiveContainer>
          <p className="small">Average of 10 snapshots per season from NASA SMAP (9 km grid).</p>
        </div>
      </div>
      <p className="small muted" style={{ marginTop: 16 }}>
        Satellites measure a whole 10 km cell, not your exact field. A rain gauge or soil probe on the farm is more exact
        for one spot — combining both gives the best picture.
      </p>
    </div>
  )
}
