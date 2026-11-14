import { useState } from 'react'
import { getField, getStrategies } from './api'
import Header from './components/Header'
import Footer from './components/Footer'
import FieldPage from './pages/FieldPage'
import ConditionsPage from './pages/ConditionsPage'
import ComparePage from './pages/ComparePage'
import DetailsPage from './pages/DetailsPage'
import HowItWorks from './pages/HowItWorks'

export default function App() {
  // Сторінки: field -> conditions -> compare -> details; how = "How it works"
  const [page, setPage] = useState('field')
  const [location, setLocation] = useState({ lat: 42.1, lon: -93.55 })
  const [priorities, setPriorities] = useState({ water: 4, soil: 5, erosion: 4, income: 3 })
  const [constraints, setConstraints] = useState({ irrigation: false, livestock: false, small_grain_equipment: false })
  const [scenario, setScenario] = useState('normal')

  const [field, setField] = useState(null)
  const [strategies, setStrategies] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [isMock, setIsMock] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function analyze() {
    setLoading(true)
    setError('')
    try {
      const fieldResult = await getField(location.lat, location.lon)
      const strategyResult = await getStrategies({ ...location, priorities, constraints, scenario: 'normal' })
      setField(fieldResult.data)
      setStrategies(strategyResult.data.strategies)
      setIsMock(fieldResult.isMock || strategyResult.isMock)
      setScenario('normal')
      setPage('conditions')
    } catch (e) {
      setError(`Could not analyze this point: ${e.message}`)
    }
    setLoading(false)
  }

  async function changeScenario(newScenario) {
    setScenario(newScenario)
    try {
      const result = await getStrategies({ ...location, priorities, constraints, scenario: newScenario })
      setStrategies(result.data.strategies)
    } catch (e) {
      console.error(e)
    }
  }

  function openDetails(id) {
    setSelectedId(id)
    setPage('details')
  }

  return (
    <>
      <Header page={page} setPage={setPage} hasData={Boolean(field)} />
      <main className="container page">
        {isMock && page !== 'field' && (
          <div className="banner">Backend is not running — showing sample data for an Iowa field.</div>
        )}
        {page === 'field' && (
          <FieldPage
            location={location} setLocation={setLocation}
            priorities={priorities} setPriorities={setPriorities}
            constraints={constraints} setConstraints={setConstraints}
            onAnalyze={analyze} loading={loading} error={error}
          />
        )}
        {page === 'conditions' && field && (
          <ConditionsPage field={field} current={strategies[0]} onNext={() => setPage('compare')} />
        )}
        {page === 'compare' && strategies && (
          <ComparePage
            strategies={strategies} field={field}
            scenario={scenario} onScenario={changeScenario} onOpen={openDetails}
          />
        )}
        {page === 'details' && strategies && (
          <DetailsPage
            strategy={strategies.find((s) => s.id === selectedId)}
            onBack={() => setPage('compare')}
          />
        )}
        {page === 'how' && <HowItWorks />}
      </main>
      <Footer />
    </>
  )
}
