import { useState } from 'react'
import Navbar from './components/Navbar'
import GamePredictions from './components/GamePredictions'
import MvpRankings from './components/MvpRankings'
import MvpChat from './components/MvpChat'
import './App.css'

function App() {
  const getInitialTab = () => {
    const hash = window.location.hash.replace('#', '')
    return ['games', 'mvp'].includes(hash) ? hash : 'games'
  }

  const [activeTab, setActiveTab] = useState(getInitialTab)

  const handleTabChange = (tab) => {
    window.location.hash = tab
    setActiveTab(tab)
  }

  return (
    <div className="app">
      <Navbar activeTab={activeTab} setActiveTab={handleTabChange} />
      <main className="main-content">
        {activeTab === 'games' && <GamePredictions />}
        {activeTab === 'mvp' && <MvpRankings />}
      </main>
      <footer className="footer">
        <p>Data from NBA Stats API | Predictions are for entertainment purposes only</p>
      </footer>
      <MvpChat />
    </div>
  )
}

export default App
