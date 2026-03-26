import { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api'
const FALLBACK_LOGO = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"><rect width="40" height="40" rx="8" fill="%231d428a"/><text x="20" y="26" text-anchor="middle" fill="white" font-size="16">🏀</text></svg>'

export default function GamePredictions() {
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API_BASE}/predictions/games`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch predictions')
        return res.json()
      })
      .then(data => {
        setPredictions(data.predictions || [])
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) return <div className="loading">Loading game predictions...</div>
  if (error) return <div className="error">Error: {error}</div>
  if (predictions.length === 0) return <div className="empty">No upcoming games to predict</div>

  return (
    <div className="predictions-container">
      <h2>🏀 Game Predictions</h2>
      <p className="subtitle">Upcoming NBA games with predicted outcomes</p>

      <div className="games-grid">
        {predictions.map((game, i) => {
          const homeWins = game.predicted_winner === game.home_team
          return (
            <div key={i} className="game-card">
              <div className="matchup">
                <div className={`team ${!homeWins ? 'winner' : ''}`}>
                  <img
                    className="team-logo"
                    src={game.away_logo}
                    alt={game.away_team}
                    onError={e => { e.target.onerror = null; e.target.src = FALLBACK_LOGO }}
                  />
                  <span className="team-name">{game.away_team}</span>
                  <span className="team-record">{game.away_season_record}</span>
                  <span className="team-prob">{game.away_win_prob}%</span>
                </div>

                <div className="vs">@</div>

                <div className={`team ${homeWins ? 'winner' : ''}`}>
                  <img
                    className="team-logo"
                    src={game.home_logo}
                    alt={game.home_team}
                    onError={e => { e.target.onerror = null; e.target.src = FALLBACK_LOGO }}
                  />
                  <span className="team-name">{game.home_team}</span>
                  <span className="team-record">{game.home_season_record}</span>
                  <span className="team-prob">{game.home_win_prob}%</span>
                </div>
              </div>

              {/* Win probability split bar */}
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
                <div className="predicted-winner">
                  🏆 {game.predicted_winner}
                </div>
                <div className="confidence-bar-container">
                  <div
                    className="confidence-bar"
                    style={{ width: `${game.confidence}%` }}
                  />
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
    </div>
  )
}
