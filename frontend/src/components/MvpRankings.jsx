import { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api'
const FALLBACK_HEADSHOT = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50"><circle cx="25" cy="25" r="25" fill="%231a2634"/><text x="25" y="32" text-anchor="middle" fill="%238899aa" font-size="22">👤</text></svg>'
const FALLBACK_TEAM_LOGO = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><rect width="20" height="20" rx="4" fill="%231d428a"/><text x="10" y="14" text-anchor="middle" fill="white" font-size="10">🏀</text></svg>'

export default function MvpRankings() {
  const [rankings, setRankings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API_BASE}/predictions/mvp`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch MVP rankings')
        return res.json()
      })
      .then(data => {
        setRankings(data.rankings || [])
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) return <div className="loading">Loading MVP rankings...</div>
  if (error) return <div className="error">Error: {error}</div>
  if (rankings.length === 0) return <div className="empty">No MVP data available</div>

  const topScore = rankings[0]?.mvp_score || 1

  return (
    <div className="mvp-container">
      <h2>🏆 MVP Race</h2>
      <p className="subtitle">Current MVP candidates ranked by composite score</p>

      <div className="mvp-table-wrapper">
        <table className="mvp-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Player</th>
              <th>Team</th>
              <th>PPG</th>
              <th>RPG</th>
              <th>APG</th>
              <th>EFF</th>
              <th>GP</th>
              <th>Team W%</th>
              <th>Seed</th>
              <th>Archetype</th>
              <th>MVP Score</th>
            </tr>
          </thead>
          <tbody>
            {rankings.map((player) => (
              <tr key={player.rank} className={player.rank <= 3 ? 'top-3' : ''}>
                <td className="rank">
                  {player.rank <= 3 ? ['🥇', '🥈', '🥉'][player.rank - 1] : player.rank}
                </td>
                <td className="player-cell">
                  <img
                    className="player-headshot"
                    src={player.headshot_url}
                    alt={player.name}
                    onError={e => { e.target.onerror = null; e.target.src = FALLBACK_HEADSHOT }}
                  />
                  <span className="player-name">
                    {player.name}
                    {player.factors.previous_mvp_bonus && <span className="mvp-badge" title="Previous MVP">⭐</span>}
                  </span>
                </td>
                <td className="team-cell">
                  <img
                    className="team-logo-sm"
                    src={player.team_logo_url}
                    alt={player.team}
                    onError={e => { e.target.onerror = null; e.target.src = FALLBACK_TEAM_LOGO }}
                  />
                  <span>{player.team}</span>
                </td>
                <td>{player.ppg}</td>
                <td>{player.rpg}</td>
                <td>{player.apg}</td>
                <td>{player.efficiency}</td>
                <td>{player.games}</td>
                <td>{player.team_win_pct}%</td>
                <td>{player.team_seed}</td>
                <td>
                  <div className="archetype-bar-container">
                    <div
                      className="archetype-bar"
                      style={{ width: `${player.archetype_similarity}%` }}
                    />
                    <span>{player.archetype_similarity}%</span>
                  </div>
                </td>
                <td>
                  <div className="score-bar-container">
                    <div
                      className="score-bar"
                      style={{ width: `${(player.mvp_score / topScore) * 100}%` }}
                    />
                    <span className="score-value">{player.mvp_score}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mvp-legend">
        <h3>How MVP Score is Calculated</h3>
        <ul>
          <li><strong>Scoring (30%)</strong> — Points per game relative to top players</li>
          <li><strong>Team Success (25%)</strong> — Team seed and win percentage</li>
          <li><strong>Archetype Match (15%)</strong> — Similarity to historical MVP winners</li>
          <li><strong>Assists (10%)</strong> — Playmaking ability</li>
          <li><strong>Efficiency (10%)</strong> — Overall stat efficiency rating</li>
          <li><strong>Rebounds (5%)</strong> — Rebounding contribution</li>
          <li><strong>Games Played (5%)</strong> — Availability and durability</li>
          <li><strong>⭐ Previous MVP</strong> — Small bonus for recent MVP winners maintaining elite play</li>
        </ul>
      </div>
    </div>
  )
}
