import { Bar, CartesianGrid, ComposedChart, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import SatelliteCard from '../components/SatelliteCard'

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function StatCard({ label, value, note, water }) {
  return (
    <div className="card">
      <div className="stat-label">{label}</div>
      <div className={'stat-value' + (water ? ' water' : '')}>{value}</div>
      <div className="stat-note">{note}</div>
    </div>
  )
}

// Які місяці першого року поточної сівозміни поле вкрите культурою
// (те саме правило, що на бекенді: культура стоїть хоча б половину місяця)
function coveredMonths(calendar) {
  return MONTH_NAMES.map((_, i) => {
    const month = i + 1
    const overlap = calendar
      .filter((bar) => bar.year === 1)
      .reduce((sum, bar) => sum + Math.max(0, Math.min(bar.end, month + 1) - Math.max(bar.start, month)), 0)
    return overlap >= 0.5
  })
}

function Trend({ title, unit, data, change, color }) {
  return (
    <div>
      <h3>{title}</h3>
      <p className="small muted">{unit}</p>
      <ResponsiveContainer width="100%" height={110}>
        <LineChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
          <XAxis dataKey="year" ticks={[data[0].year, data[data.length - 1].year]} tick={{ fontSize: 12 }} />
          <YAxis domain={['auto', 'auto']} tick={{ fontSize: 12 }} />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke={color} dot={false} strokeWidth={1.5} />
        </LineChart>
      </ResponsiveContainer>
      <p className="small">{change}</p>
    </div>
  )
}

function signed(value) {
  return (value > 0 ? '+' : '') + value
}

export default function ConditionsPage({ field, current, onNext }) {
  const { climate, soil, location } = field
  const months = climate.monthly.map((m) => ({ ...m, name: MONTH_NAMES[m.month - 1] }))
  const covered = coveredMonths(current.calendar)
  const bareCount = covered.filter((c) => !c).length

  // Попередження генеруємо з даних
  const warnings = []
  if (climate.late_frost_years_per_10 >= 2) {
    warnings.push({ title: 'Late spring frost', text: `Last frost came after May 5 in ${climate.late_frost_years_per_10} of 10 years.` })
  }
  if (bareCount >= 4) {
    warnings.push({ title: 'Uncovered soil', text: `Soil is bare about ${bareCount} months a year, when heavy rain can wash topsoil away.`, high: bareCount >= 6 })
  }
  if (climate.heat_days_35c >= 3) {
    warnings.push({ title: 'Hot days', text: `${climate.heat_days_35c} days above 35 °C per year can stress crops when soils are dry.` })
  }
  if (climate.trends.season_rain_mm_per_decade < -5) {
    warnings.push({ title: 'Less summer rain', text: `May–Sep rain is changing by ${climate.trends.season_rain_mm_per_decade} mm per decade.` })
  }

  return (
    <>
      <div className="page-title-row">
        <div>
          <h1>Your field at a glance</h1>
          <p className="muted">{location.area || 'Selected field'} · {location.lat.toFixed(2)}, {location.lon.toFixed(2)}</p>
        </div>
        <p className="muted">Current rotation: {current.name}</p>
      </div>

      {field.warnings?.map((w) => <div className="banner" key={w}>{w}</div>)}

      <div className="grid-5">
        <StatCard
          label="Frost-free season"
          value={climate.last_spring_frost ? `${climate.frost_free_days} days` : 'All year'}
          note={climate.last_spring_frost ? `${climate.last_spring_frost} to ${climate.first_fall_frost}` : 'Frost is rare here'}
        />
        <StatCard label="Growing degree days" value={climate.gdd_base10.toLocaleString('en-US')} note="base 10 °C, Apr–Oct" />
        <StatCard label="Season rainfall" value={`${climate.season_rain_mm} mm`} note="May–Sep, typical year" water />
        <StatCard label="Heat days" value={climate.heat_days_35c} note="above 35 °C per year" />
        <StatCard
          label="Soil"
          value={soil ? soil.name : '—'}
          note={soil ? `${soil.organic_matter_pct}% organic matter, ${soil.slope_pct}% slope` : 'Soil data not available'}
        />
      </div>

      <div className="card">
        <h2>A typical year on this field</h2>
        <p className="card-subtitle">Monthly averages, {climate.source}</p>
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={months} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
            <CartesianGrid vertical={false} stroke="#e2ded5" />
            <XAxis dataKey="name" />
            <YAxis yAxisId="rain" label={{ value: 'Rainfall (mm)', angle: -90, position: 'insideLeft' }} />
            <YAxis yAxisId="temp" orientation="right" label={{ value: 'Temperature (°C)', angle: 90, position: 'insideRight' }} />
            <Tooltip />
            <Bar yAxisId="rain" dataKey="rain_mm" name="Rainfall, mm" fill="#2f6690" />
            <Line yAxisId="temp" dataKey="tavg" name="Avg temperature, °C" stroke="#1f2421" strokeWidth={2} />
          </ComposedChart>
        </ResponsiveContainer>
        <div className="cover-band">
          {covered.map((isCovered, i) => (
            <div key={i} style={{ flex: 1, background: isCovered ? '#3f6b3a' : '#d9c8a6' }} />
          ))}
        </div>
        <div className="legend" style={{ marginLeft: 60 }}>
          <span><span className="legend-dot" style={{ background: '#d9c8a6' }} />Bare soil: {bareCount} months</span>
          <span><span className="legend-dot" style={{ background: '#3f6b3a' }} />Crop cover</span>
          <span>Shown for year 1 of the current rotation.</span>
        </div>
      </div>

      <div className="grid-2" style={{ marginTop: 24 }}>
        <div className="card">
          <h2>What changed in {climate.years} years</h2>
          <p className="card-subtitle">Yearly values, {climate.source}. Root-zone wetness is a model estimate (0 = dry, 1 = saturated).</p>
          <div className="grid-3">
            <Trend title="Summer max temperature" unit="°C, Jun–Aug average" data={climate.series.summer_tmax}
              change={`${signed(climate.trends.summer_tmax_c_per_decade)} °C per decade`} color="#1f2421" />
            <Trend title="Season rainfall" unit="mm, May–Sep" data={climate.series.season_rain}
              change={`${signed(climate.trends.season_rain_mm_per_decade)} mm per decade`} color="#2f6690" />
            <Trend title="Root-zone soil wetness" unit="0–1, May–Sep" data={climate.series.season_soil}
              change={`${signed(climate.trends.soil_wetness_per_decade)} per decade`} color="#2f6690" />
          </div>
        </div>

        <div className="card">
          <h2>Things to watch</h2>
          <p className="card-subtitle">Planning cautions for this field</p>
          {warnings.length === 0 && <p className="muted">No major warnings from the climate record.</p>}
          {warnings.map((w) => (
            <div className={'watch-item' + (w.high ? ' high' : '')} key={w.title}>
              <h3>{w.title}</h3>
              <p className="small muted">{w.text}</p>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 24 }}>
        <SatelliteCard lat={location.lat} lon={location.lon} powerRain={climate.series.season_rain} />
      </div>

      <div className="cta">
        <div>
          <h2>Ready to weigh your options?</h2>
          <p className="muted">Compare rotations using this field's conditions and your priorities.</p>
        </div>
        <button className="button" onClick={onNext}>Compare rotation options</button>
      </div>
    </>
  )
}
