// Звернення до бекенду.
// Якщо бекенд узагалі не запущений — повертаємо мок-дані (поле в Айові), щоб фронтенд можна було
// розробляти окремо. Якщо бекенд відповів помилкою (наприклад, точка в океані) — показуємо цю помилку.
import mockField from './mocks/field.json'
import mockStrategies from './mocks/strategies.json'

const BACKEND_DOWN = 'backend-down'

async function request(url, options) {
  let response
  try {
    response = await fetch(url, options)
  } catch {
    throw new Error(BACKEND_DOWN) // мережа: бекенд не відповідає
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    // FastAPI завжди повертає {"detail": ...}. Без нього — це Vite не зміг достукатись до бекенду.
    throw new Error(body?.detail || BACKEND_DOWN)
  }
  return response.json()
}

export async function getField(lat, lon) {
  try {
    return { data: await request(`/api/field?lat=${lat}&lon=${lon}`), isMock: false }
  } catch (error) {
    if (error.message !== BACKEND_DOWN) throw error
    console.warn('Backend not available, using mock field data')
    return { data: mockField, isMock: true }
  }
}

export async function getStrategies({ lat, lon, priorities, constraints, scenario }) {
  const options = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lat, lon, priorities, constraints, scenario }),
  }
  try {
    return { data: await request('/api/strategies', options), isMock: false }
  } catch (error) {
    if (error.message !== BACKEND_DOWN) throw error
    console.warn('Backend not available, using mock strategies')
    return { data: mockStrategies, isMock: true }
  }
}

// Супутникові дані NASA (IMERG, SMAP). Для нового поля це до 2 хвилин, тому вантажимо окремо.
export async function getSatellite(lat, lon) {
  return request(`/api/satellite?lat=${lat}&lon=${lon}`)
}

// Пошук місця за назвою або адресою (тільки США). null — якщо нічого не знайдено.
export async function geocode(query) {
  try {
    return await request(`/api/geocode?q=${encodeURIComponent(query)}`)
  } catch (error) {
    if (error.message === 'Place not found') return null
    throw error
  }
}
