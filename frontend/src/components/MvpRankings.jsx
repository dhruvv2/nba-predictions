import { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api'
const FALLBACK_HEADSHOT = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50"><circle cx="25" cy="25" r="25" fill="%231a2634"/><text x="25" y="32" text-anchor="middle" fill="%238899aa" font-size="22">👤</text></svg>'
const FALLBACK_TEAM_LOGO = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><rect width="20" height="20" rx="4" fill="%231d428a"/><text x="10" y="14" text-anchor="middle" fill="white" font-size="10">🏀</text></svg>'

const ELIGIBILITY_BADGES = {
  eligible: { icon: '✅', label: 'Eligible (65+ GP)', cls: 'elig-ok' },
  projected: { icon: '⏳', label: 'On pace for 65 GP', cls: 'elig-proj' },
  ineligible: { icon: '❌', label: 'Ineligible (<65 GP pace)', cls: 'elig-no' },
}

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
      <h2>🏆 KIA MVP Race — 2025-26 Season</h2>
      <p className="subtitle">MVP candidates ranked by composite score (65-game rule applied)</p>

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
              <th>FG%</th>
              <th>GP</th>
              <th>Seed</th>
              <th>Status</th>
              <th>MVP Score</th>
            </tr>
          </thead>
          <tbody>
            {rankings.map((player) => {
              const badge = ELIGIBILITY_BADGES[player.eligibility] || ELIGIBILITY_BADGES.projected
              return (
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
                  <td>{player.fg_pct}%</td>
                  <td>{player.games}</td>
                  <td>{player.team_seed}</td>
                  <td>
                    <span className={`eligibility-badge ${badge.cls}`} title={badge.label}>
                      {badge.icon}
                    </span>
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
              )
            })}
          </tbody>
        </table>
      </div>

      <div className="mvp-legend">
        <h3>How MVP Score is Calculated</h3>
        <ul>
          <li><strong>Scoring (25%)</strong> — Points per game relative to top candidates</li>
          <li><strong>All-Around (20%)</strong> — Combined PTS + REB + AST impact (rewards triple-double types)</li>
          <li><strong>Team Success (20%)</strong> — Playoff seed and win percentage</li>
          <li><strong>Archetype Match (15%)</strong> — Similarity to historical MVP stat profiles</li>
          <li><strong>Availability (10%)</strong> — Games played (65-game rule since 2023-24)</li>
          <li><strong>Efficiency (10%)</strong> — Field goal percentage</li>
          <li><strong>⭐ Previous MVP</strong> — Small bonus for recent MVP winners</li>
        </ul>
        <div className="eligibility-legend">
          <h4>Eligibility Status (65-Game Rule)</h4>
          <p>✅ Eligible — 65+ games played &nbsp; ⏳ Projected — On pace for 65 GP &nbsp; ❌ Ineligible — Won't reach 65 GP</p>
        </div>
      </div>
    </div>
  )
}
