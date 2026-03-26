import { useState } from 'react'
import Navbar from './components/Navbar'
import GamePredictions from './components/GamePredictions'
import MvpRankings from './components/MvpRankings'
import LiveScores from './components/LiveScores'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('games')

  return (
    <div className="app">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="main-content">
        {activeTab === 'games' && <GamePredictions />}
        {activeTab === 'mvp' && <MvpRankings />}
        {activeTab === 'live' && <LiveScores />}
      </main>
      <footer className="footer">
        <p>Data sourced from basketball-reference.com | Predictions are for entertainment purposes</p>
      </footer>
    </div>
  )
}

export default App
