// Календар сівозміни: рядок на кожен рік, смуги культур по місяцях.
// Дані приходять з бекенду: calendar = [{year, crop, name, kind, start, end}], start/end — місяці 1..13.

export const CROP_COLORS = {
  corn: '#c9a227',
  soybean: '#3f6b3a',
  winter_wheat: '#b5895a',
  spring_wheat: '#b5895a',
  oats: '#a3a86b',
  sorghum: '#a1392b',
  sunflower: '#e0b43a',
  cotton: '#8c8c8c',
  alfalfa: '#6a8f4e',
  cereal_rye: '#7d6b4f',
  clover: '#9b5d7a',
}

const MONTHS = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']

export default function RotationCalendar({ calendar }) {
  const years = Math.max(...calendar.map((bar) => bar.year))
  const crops = [...new Map(calendar.map((bar) => [bar.crop, bar.name])).entries()]

  return (
    <div className="calendar">
      {Array.from({ length: years }, (_, i) => i + 1).map((year) => (
        <div className="calendar-row" key={year}>
          <span className="calendar-label">Y{year}</span>
          <div className="calendar-track">
            {calendar.filter((bar) => bar.year === year).map((bar, i) => (
              <div
                key={i}
                className={'calendar-bar' + (bar.kind === 'cover' ? ' cover' : '')}
                title={bar.name}
                style={{
                  left: `${((bar.start - 1) / 12) * 100}%`,
                  width: `${((bar.end - bar.start) / 12) * 100}%`,
                  background: CROP_COLORS[bar.crop] || '#999',
                }}
              />
            ))}
          </div>
        </div>
      ))}
      <div className="calendar-months">
        {MONTHS.map((m, i) => <span key={i}>{m}</span>)}
      </div>
      <div className="legend" style={{ flexWrap: 'wrap', gap: 12, marginTop: 8 }}>
        {crops.map(([id, name]) => (
          <span key={id}><span className="legend-dot" style={{ background: CROP_COLORS[id] }} />{name}</span>
        ))}
      </div>
    </div>
  )
}
