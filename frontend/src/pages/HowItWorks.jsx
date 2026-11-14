// TODO (роль 3): дописати глосарій і пояснення методу простими словами.

const GLOSSARY = [
  ['Growing degree days (GDD)', 'Heat a crop gets over the season: each day adds the average temperature minus 10 °C. Crops need a certain total to mature.'],
  ['Frost-free season', 'Days between the last spring frost and the first fall frost (minimum temperature at or below 0 °C).'],
  ['Evapotranspiration (ET)', 'Water that leaves the field as vapour from soil and plant leaves. More ET means the crop needs more water.'],
  ['Root-zone soil wetness', 'How wet the soil is where roots grow, from 0 (dry) to 1 (saturated). From the NASA POWER model.'],
  ['NDVI', 'A satellite index of how green and dense plants are. Low NDVI in summer can mean stress or bare soil.'],
  ['Cover crop', 'A crop grown between cash crops to protect and feed the soil, not for sale.'],
  ['Nitrogen-fixing crop', 'Legumes like soybean, clover and alfalfa take nitrogen from the air and leave some for the next crop.'],
]

export default function HowItWorks() {
  return (
    <div className="stack">
      <div>
        <h1>How it works</h1>
        <p className="muted">Field Shift compares crop rotations for one field using public NASA and USDA data.</p>
      </div>

      <div className="card">
        <h2>Steps</h2>
        <ol>
          <li>We read 31 years of daily weather for your point from NASA POWER and turn it into frost dates, heat days, rainfall and trends.</li>
          <li>We read your soil (organic matter, slope, erosion factor) from USDA SSURGO.</li>
          <li>We detect your current rotation from USDA Cropland Data Layer maps of the last 10 years.</li>
          <li>We build three alternatives and score all options from 0 to 100 on six criteria, weighted by your priorities.</li>
        </ol>
      </div>

      <div className="card">
        <h2>Satellite and model data vs. field measurements</h2>
        <p>
          Satellites and models cover every field, but they average over areas from 30 m to 50 km and can miss local details.
          Ground measurements, like a rain gauge or a soil test on your farm, are more exact for one spot. The best picture comes from combining both.
        </p>
      </div>

      <div className="card">
        <h2>Glossary</h2>
        {GLOSSARY.map(([term, text]) => (
          <div className="evidence-row" key={term}>
            <strong style={{ minWidth: 240 }}>{term}</strong>
            <span>{text}</span>
          </div>
        ))}
      </div>

      <div className="card check-local">
        <h2>Limits of this tool</h2>
        <p>
          Scores are simple rules based on public data and typical crop traits. They do not know your equipment, contracts,
          pests or local markets. Use them to start a conversation with your agronomist or extension office, not as a final answer.
        </p>
      </div>
    </div>
  )
}
