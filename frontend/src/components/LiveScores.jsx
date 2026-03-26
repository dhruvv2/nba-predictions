import { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api'
const FALLBACK_LOGO = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"><rect width="40" height="40" rx="8" fill="%231d428a"/><text x="20" y="26" text-anchor="middle" fill="white" font-size="16">🏀</text></svg>'

export default function LiveScores() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  const fetchScores = () => {
    fetch(`${API_BASE}/scores/live`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch live scores')
        return res.json()
      })
      .then(result => {
        setData(result)
        setLastUpdated(new Date())
        setLoading(false)
        setError(null)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }

  useEffect(() => {
    fetchScores()
    const interval = setInterval(fetchScores, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) return <div className="loading">Loading live scores...</div>
  if (error) return <div className="error">Error: {error}</div>

  const games = data?.games || []

  const isLive = (status) => {
    if (!status) return false
    const s = status.toLowerCase()
    return !s.includes('final') && !s.includes('scheduled') && !s.includes('not started')
  }

  return (
    <div className="live-container">
      <div className="live-header">
        <h2>📺 Live Scores</h2>
        <div className="live-meta">
          {lastUpdated && (
            <span className="last-updated">
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <span className="auto-refresh-badge">Auto-refreshes every 30s</span>
        </div>
      </div>
      <p className="subtitle">{data?.date || "Today's games"}</p>

      {games.length === 0 ? (
        <div className="empty">No games scheduled today</div>
      ) : (
        <div className="live-grid">
          {games.map((game) => (
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
                  <img
                    className="team-logo"
                    src={game.away_logo}
                    alt={game.away_team}
                    onError={e => { e.target.onerror = null; e.target.src = FALLBACK_LOGO }}
                  />
                  <span className="live-team-name">{game.away_team}</span>
                  <span className="live-score">{game.away_score ?? '—'}</span>
                </div>

                <div className="live-team">
                  <img
                    className="team-logo"
                    src={game.home_logo}
                    alt={game.home_team}
                    onError={e => { e.target.onerror = null; e.target.src = FALLBACK_LOGO }}
                  />
                  <span className="live-team-name">{game.home_team}</span>
                  <span className="live-score">{game.home_score ?? '—'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
