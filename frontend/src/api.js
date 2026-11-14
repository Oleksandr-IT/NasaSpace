// Звернення до бекенду. Якщо бекенд не запущений, повертаємо мок-дані (поле в Айові),
// щоб фронтенд можна було розробляти окремо.
import mockField from './mocks/field.json'
import mockStrategies from './mocks/strategies.json'

export async function getField(lat, lon) {
  try {
    const response = await fetch(`/api/field?lat=${lat}&lon=${lon}`)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return { data: await response.json(), isMock: false }
  } catch (error) {
    console.warn('Backend not available, using mock field data:', error)
    return { data: mockField, isMock: true }
  }
}

// Супутникові дані NASA (IMERG, SMAP). Для нового поля це до 2 хвилин, тому вантажимо окремо.
export async function getSatellite(lat, lon) {
  const response = await fetch(`/api/satellite?lat=${lat}&lon=${lon}`)
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

// Пошук місця за назвою або адресою (тільки США)
export async function geocode(query) {
  const response = await fetch(`/api/geocode?q=${encodeURIComponent(query)}`)
  if (response.status === 404) return null
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

export async function getStrategies({ lat, lon, priorities, constraints, scenario }) {
  try {
    const response = await fetch('/api/strategies', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat, lon, priorities, constraints, scenario }),
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return { data: await response.json(), isMock: false }
  } catch (error) {
    console.warn('Backend not available, using mock strategies:', error)
    return { data: mockStrategies, isMock: true }
  }
}
