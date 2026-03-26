import { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api'
const FALLBACK_LOGO = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"><rect width="40" height="40" rx="8" fill="%231d428a"/><text x="20" y="26" text-anchor="middle" fill="white" font-size="16">🏀</text></svg>'

export default function GamePredictions() {
  const [predictions, setPredictions] = useState([])
  const [liveGames, setLiveGames] = useState([])
  const [liveDate, setLiveDate] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  const fetchLiveScores = () => {
    fetch(`${API_BASE}/scores/live`)
      .then(res => res.ok ? res.json() : { games: [] })
      .then(data => {
        setLiveGames(data.games || [])
        setLiveDate(data.date || '')
        setLastUpdated(new Date())
      })
      .catch(() => {})
  }

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/predictions/games`).then(r => r.json()),
      fetch(`${API_BASE}/scores/live`).then(r => r.json()).catch(() => ({ games: [] }))
    ])
      .then(([predData, liveData]) => {
        setPredictions(predData.predictions || [])
        setLiveGames(liveData.games || [])
        setLiveDate(liveData.date || '')
        setLastUpdated(new Date())
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })

    const interval = setInterval(fetchLiveScores, 30000)
    return () => clearInterval(interval)
  }, [])

  const isLive = (status) => {
    if (!status) return false
    const s = status.toLowerCase()
    return !s.includes('final') && !s.includes('scheduled') && !s.includes('not started') && s.trim() !== ''
  }

  if (loading) return <div className="loading">Loading games...</div>
  if (error) return <div className="error">Error: {error}</div>

  const liveCount = liveGames.filter(g => isLive(g.status)).length

  return (
    <div className="predictions-container">
      {/* Live Scores Section */}
      {liveGames.length > 0 && (
        <section className="live-section">
          <div className="live-header">
            <h2>
              {liveCount > 0 && <span className="pulse-dot" />}
              {liveCount > 0 ? ' Live Games' : '📺 Today\'s Games'}
            </h2>
            <div className="live-meta">
              {lastUpdated && (
                <span className="last-updated">Updated {lastUpdated.toLocaleTimeString()}</span>
              )}
              <span className="auto-refresh-badge">Auto-refreshes every 30s</span>
            </div>
          </div>
          <p className="subtitle">{liveDate}</p>

          <div className="live-grid">
            {liveGames.map((game) => (
              <div key={game.game_id} className={`live-card ${isLive(game.status) ? 'live-active' : ''}`}>
                {isLive(game.status) && (
                  <div className="live-indicator">
                    <span className="pulse-dot" />
                    <span className="live-text">LIVE</span>
                  </div>
                )}
                <div className="live-status">{game.status}</div>
                <div className="live-matchup">
                  <div className="live-team">
                    <img className="team-logo" src={game.away_logo} alt={game.away_team}
                      onError={e => { e.target.onerror = null; e.target.src = FALLBACK_LOGO }} />
                    <span className="live-team-name">{game.away_team}</span>
                    <span className="live-score">{game.away_score ?? '—'}</span>
                  </div>
                  <div className="live-team">
                    <img className="team-logo" src={game.home_logo} alt={game.home_team}
                      onError={e => { e.target.onerror = null; e.target.src = FALLBACK_LOGO }} />
                    <span className="live-team-name">{game.home_team}</span>
                    <span className="live-score">{game.home_score ?? '—'}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Upcoming Game Predictions */}
      <section className="upcoming-section">
        <h2>🏀 Upcoming Game Predictions</h2>
        <p className="subtitle">Predicted outcomes for upcoming NBA games</p>

        {predictions.length === 0 ? (
          <div className="empty">No upcoming games to predict</div>
        ) : (
          <div className="games-grid">
            {predictions.map((game, i) => {
              const homeWins = game.predicted_winner === game.home_team
              return (
                <div key={i} className="game-card">
                  <div className="matchup">
                    <div className={`team ${!homeWins ? 'winner' : ''}`}>
                      <img className="team-logo" src={game.away_logo} alt={game.away_team}
                        onError={e => { e.target.onerror = null; e.target.src = FALLBACK_LOGO }} />
                      <span className="team-name">{game.away_team}</span>
                      <span className="team-record">{game.away_season_record}</span>
                      <span className="team-prob">{game.away_win_prob}%</span>
                    </div>
                    <div className="vs">@</div>
                    <div className={`team ${homeWins ? 'winner' : ''}`}>
                      <img className="team-logo" src={game.home_logo} alt={game.home_team}
                        onError={e => { e.target.onerror = null; e.target.src = FALLBACK_LOGO }} />
                      <span className="team-name">{game.home_team}</span>
                      <span className="team-record">{game.home_season_record}</span>
                      <span className="team-prob">{game.home_win_prob}%</span>
                    </div>
                  </div>

                  <div className="prob-bar-wrapper">
                    <div className="prob-bar-container">
                      <div className="prob-bar away" style={{ width: `${game.away_win_prob}%` }} />
                      <div className="prob-bar home" style={{ width: `${game.home_win_prob}%` }} />
                    </div>
                    <div className="prob-labels">
                      <span>{game.away_win_prob}%</span>
                      <span>{game.home_win_prob}%</span>
                    </div>
                  </div>

                  <div className="prediction-result">
                    <div className="predicted-winner">🏆 {game.predicted_winner}</div>
                    <div className="confidence-bar-container">
                      <div className="confidence-bar" style={{ width: `${game.confidence}%` }} />
                      <span className="confidence-label">{game.confidence}% confidence</span>
                    </div>
                  </div>

                  <details className="factors">
                    <summary>View factors</summary>
                    <ul>
                      <li>Home strength: {game.factors.home_strength}</li>
                      <li>Away strength: {game.factors.away_strength}</li>
                      <li>Home win prob: {game.factors.home_win_probability}%</li>
                      <li>Home court: {game.factors.home_court_advantage}</li>
                      <li>H2H: {game.factors.head_to_head}</li>
                      <li>Home L10: {game.factors.home_recent_form}</li>
                      <li>Away L10: {game.factors.away_recent_form}</li>
                    </ul>
                  </details>
                </div>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}
