export default function Navbar({ activeTab, setActiveTab }) {
  return (
    <nav className="navbar">
      <div className="nav-brand">
        <span className="logo">🏀</span>
        <h1>NBA Predictions</h1>
      </div>
      <div className="nav-tabs">
        <button
          className={`nav-tab ${activeTab === 'games' ? 'active' : ''}`}
          onClick={() => setActiveTab('games')}
        >
          🔴 Games & Live Scores
        </button>
        <button
          className={`nav-tab ${activeTab === 'mvp' ? 'active' : ''}`}
          onClick={() => setActiveTab('mvp')}
        >
          🏆 MVP Race
        </button>
      </div>
    </nav>
  )
}
