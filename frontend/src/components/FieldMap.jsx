import { useState } from 'react'
import { CircleMarker, MapContainer, TileLayer, Tooltip, useMap, useMapEvents } from 'react-leaflet'

// Шари NASA GIBS (те саме, що в NASA Worldview). Акаунт не потрібен.
// Це картинки для перегляду, а не числа для розрахунків.
const NASA_LAYERS = {
  none: null,
  smap: { name: 'SMAP root-zone soil moisture', id: 'SMAP_L4_Analyzed_Root_Zone_Soil_Moisture', matrix: 'GoogleMapsCompatible_Level6', maxZoom: 6 },
  ndvi: { name: 'MODIS vegetation (NDVI, 8-day)', id: 'MODIS_Terra_NDVI_8Day', matrix: 'GoogleMapsCompatible_Level9', maxZoom: 9 },
  imerg: { name: 'GPM IMERG rain rate', id: 'IMERG_Precipitation_Rate', matrix: 'GoogleMapsCompatible_Level6', maxZoom: 6 },
}

function ClickHandler({ onPick }) {
  useMapEvents({ click: (e) => onPick(e.latlng.lat, e.latlng.lng) })
  return null
}

// Коли вибирають інше демо-поле, переміщуємо карту до нього
function FlyTo({ lat, lon }) {
  const map = useMap()
  map.setView([lat, lon], map.getZoom())
  return null
}

export default function FieldMap({ lat, lon, label, onPick }) {
  const [layer, setLayer] = useState('none')
  const [date, setDate] = useState('2025-07-12')
  const nasa = NASA_LAYERS[layer]

  return (
    <>
      <MapContainer center={[lat, lon]} zoom={10} className="map">
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
          attribution="Map tiles &copy; Esri and contributors"
        />
        {nasa && (
          <TileLayer
            key={layer + date}
            url={`https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${nasa.id}/default/${date}/${nasa.matrix}/{z}/{y}/{x}.png`}
            maxNativeZoom={nasa.maxZoom}
            opacity={0.6}
            attribution="NASA GIBS"
          />
        )}
        <CircleMarker center={[lat, lon]} radius={9} pathOptions={{ color: '#fff', weight: 2, fillColor: '#3f6b3a', fillOpacity: 1 }}>
          <Tooltip permanent direction="top" offset={[0, -10]}>{label}</Tooltip>
        </CircleMarker>
        <ClickHandler onPick={onPick} />
        <FlyTo lat={lat} lon={lon} />
      </MapContainer>
      <div className="map-footer">
        <span className="small muted">Click the map to choose a field</span>
        <span>
          <select className="layer-select" value={layer} onChange={(e) => setLayer(e.target.value)}>
            <option value="none">NASA layer: none</option>
            {Object.entries(NASA_LAYERS).filter(([, l]) => l).map(([key, l]) => (
              <option key={key} value={key}>{l.name}</option>
            ))}
          </select>{' '}
          {nasa && <input className="layer-select" type="date" value={date} onChange={(e) => setDate(e.target.value)} />}
        </span>
      </div>
    </>
  )
}
