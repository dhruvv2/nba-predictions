import { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api'

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
              <div className="game-date">{new Date(game.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</div>

              <div className="matchup">
                <div className={`team ${!homeWins ? 'winner' : ''}`}>
                  <span className="team-abbrev">{game.away_team}</span>
                  <span className="team-record">{game.away_win_pct}% W</span>
                </div>

                <div className="vs">@</div>

                <div className={`team ${homeWins ? 'winner' : ''}`}>
                  <span className="team-abbrev">{game.home_team}</span>
                  <span className="team-record">{game.home_win_pct}% W</span>
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
