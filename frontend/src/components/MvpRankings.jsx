import { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api'

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
                <td className="player-name">
                  {player.name}
                  {player.factors.previous_mvp_bonus && <span className="mvp-badge" title="Previous MVP">⭐</span>}
                </td>
                <td>{player.team}</td>
                <td>{player.ppg}</td>
                <td>{player.rpg}</td>
                <td>{player.apg}</td>
                <td>{player.efficiency}</td>
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
          <li><strong>Scoring (25%)</strong> — Points per game relative to top players</li>
          <li><strong>Team Success (20%)</strong> — Team seed and win percentage</li>
          <li><strong>Assists (15%)</strong> — Playmaking ability</li>
          <li><strong>Efficiency (15%)</strong> — Overall stat efficiency rating</li>
          <li><strong>Archetype Match (15%)</strong> — Similarity to historical MVP winners</li>
          <li><strong>Rebounds (10%)</strong> — Rebounding contribution</li>
          <li><strong>⭐ Previous MVP</strong> — Small bonus for recent MVP winners maintaining elite play</li>
        </ul>
      </div>
    </div>
  )
}
