import { useState } from 'react'
import Navbar from './components/Navbar'
import GamePredictions from './components/GamePredictions'
import MvpRankings from './components/MvpRankings'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('games')

  return (
    <div className="app">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="main-content">
        {activeTab === 'games' && <GamePredictions />}
        {activeTab === 'mvp' && <MvpRankings />}
      </main>
      <footer className="footer">
        <p>Data from NBA Stats API | Predictions are for entertainment purposes only</p>
      </footer>
    </div>
  )
}

export default App
