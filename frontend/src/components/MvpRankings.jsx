import { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api'
const FALLBACK_HEADSHOT = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50"><circle cx="25" cy="25" r="25" fill="%231a2634"/><text x="25" y="32" text-anchor="middle" fill="%238899aa" font-size="22">👤</text></svg>'
const FALLBACK_TEAM_LOGO = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><rect width="20" height="20" rx="4" fill="%231d428a"/><text x="10" y="14" text-anchor="middle" fill="white" font-size="10">🏀</text></svg>'

const ELIGIBILITY_BADGES = {
  eligible: { icon: '✅', label: 'Eligible — 65+ games played at 20+ min', cls: 'elig-ok' },
  projected: { icon: '⏳', label: 'Projected — On pace for 65 GP but not there yet', cls: 'elig-proj' },
  ineligible: { icon: '❌', label: 'Ineligible — Won\'t reach 65 GP at current pace', cls: 'elig-no' },
}

const COLUMNS = [
  { key: 'rank', label: '#', tooltip: 'MVP ranking position based on composite score' },
  { key: 'player', label: 'Player', tooltip: 'Player name and headshot (⭐ = previous MVP winner)' },
  { key: 'team', label: 'Team', tooltip: 'Current NBA team' },
  { key: 'ppg', label: 'PPG', tooltip: 'Points Per Game — average points scored each game' },
  { key: 'rpg', label: 'RPG', tooltip: 'Rebounds Per Game — average rebounds grabbed each game' },
  { key: 'apg', label: 'APG', tooltip: 'Assists Per Game — average assists dished each game' },
  { key: 'spg', label: 'STL', tooltip: 'Steals Per Game — measures ball-hawking defensive ability' },
  { key: 'bpg', label: 'BLK', tooltip: 'Blocks Per Game — measures rim protection and shot deterrence' },
  { key: 'ts_pct', label: 'TS%', tooltip: 'True Shooting % — scoring efficiency accounting for FGs, 3s, and FTs. League avg ~57%' },
  { key: 'pie', label: 'PIE', tooltip: 'Player Impact Estimate — overall statistical contribution. Top MVPs typically 18%+' },
  { key: 'net_rating', label: 'NET', tooltip: 'Net Rating — point differential per 100 possessions with player on court. Positive = outscoring opponents' },
  { key: 'est_ws', label: 'WS', tooltip: 'Estimated Win Shares — credits a player for their contribution to team wins. WS leader won MVP 14 of 20 seasons (2005-2024)' },
  { key: 'ast_tov', label: 'A/TO', tooltip: 'Assist-to-Turnover Ratio — ball-handling efficiency. Higher = fewer mistakes per assist' },
  { key: 'est_per', label: 'PER', tooltip: 'Estimated Player Efficiency Rating — per-minute production accounting for all box score stats. League avg = 15' },
  { key: 'est_bpm', label: 'BPM', tooltip: 'Estimated Box Plus/Minus — contribution above average per 100 possessions. MVP winners typically 8+' },
  { key: 'est_vorp', label: 'VORP', tooltip: 'Estimated Value Over Replacement Player — BPM scaled by playing time. Measures total value added vs. a replacement-level player. MVP winners typically 8+' },
  { key: 'clutch_ppg', label: 'CLU', tooltip: 'Clutch PPG — points per game in last 5 min when game within 5 pts. Measures big-moment performance' },
  { key: 'gp', label: 'GP', tooltip: 'Games Played — 65 games required for MVP eligibility (since 2023-24)' },
  { key: 'seed', label: 'Seed', tooltip: 'Team playoff seed — top-3 seed won MVP 19 of 20 times (2005-2024)' },
  { key: 'status', label: 'Status', tooltip: '65-game eligibility: ✅ Eligible, ⏳ Projected, ❌ Ineligible' },
  { key: 'ml_prob', label: 'ML%', tooltip: 'Machine Learning MVP probability — Gradient Boosting model trained on 2005-2024 MVP races (100 candidates). Higher = more likely to win MVP based on historical patterns' },
  { key: 'score', label: 'MVP Score', tooltip: 'Composite: 60% heuristic model (hand-tuned weights) + 40% ML model (gradient boosting). Scale 0-100' },
]

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
      <p className="subtitle">MVP candidates ranked by composite score including advanced stats (hover headers for explanations)</p>

      <div className="mvp-table-wrapper">
        <table className="mvp-table">
          <thead>
            <tr>
              {COLUMNS.map(col => (
                <th key={col.key} title={col.tooltip} className={`col-${col.key}`}>
                  <span className="th-label">{col.label}</span>
                  <span className="th-hint">ⓘ</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rankings.map((player) => {
              const badge = ELIGIBILITY_BADGES[player.eligibility] || ELIGIBILITY_BADGES.projected
              return (
                <tr key={player.rank} className={player.rank <= 3 ? 'top-3' : ''}>
                  <td className="col-rank">
                    {player.rank <= 3 ? ['🥇', '🥈', '🥉'][player.rank - 1] : player.rank}
                  </td>
                  <td className="col-player">
                    <div className="player-cell">
                      <img
                        className="player-headshot"
                        src={player.headshot_url}
                        alt={player.name}
                        onError={e => { e.target.onerror = null; e.target.src = FALLBACK_HEADSHOT }}
                      />
                      <span className="player-name">
                        {player.name}
                        {player.ml_probability > 0 && player.factors.narrative > 40 && <span className="mvp-badge" title="Strong narrative factor">📖</span>}
                      </span>
                    </div>
                  </td>
                  <td className="col-team">
                    <div className="team-cell">
                      <img
                        className="team-logo-sm"
                        src={player.team_logo_url}
                        alt={player.team}
                        onError={e => { e.target.onerror = null; e.target.src = FALLBACK_TEAM_LOGO }}
                      />
                    </div>
                  </td>
                  <td className="col-stat">{player.ppg}</td>
                  <td className="col-stat">{player.rpg}</td>
                  <td className="col-stat">{player.apg}</td>
                  <td className="col-stat">{player.spg}</td>
                  <td className="col-stat">{player.bpg}</td>
                  <td className="col-stat col-adv">{player.ts_pct}%</td>
                  <td className="col-stat col-adv">{player.pie}</td>
                  <td className="col-stat col-adv" style={{ color: player.net_rating >= 0 ? 'var(--success)' : 'var(--accent)' }}>
                    {player.net_rating > 0 ? '+' : ''}{player.net_rating}
                  </td>
                  <td className="col-stat col-ws">{player.est_ws}</td>
                  <td className="col-stat">{player.ast_tov}</td>
                  <td className="col-stat col-adv">{player.est_per}</td>
                  <td className="col-stat col-adv" style={{ color: player.est_bpm >= 0 ? 'var(--success)' : 'var(--accent)' }}>
                    {player.est_bpm > 0 ? '+' : ''}{player.est_bpm}
                  </td>
                  <td className="col-stat col-adv">{player.est_vorp}</td>
                  <td className="col-stat">{player.clutch_ppg || '—'}</td>
                  <td className="col-stat">{player.games}</td>
                  <td className="col-stat">{player.team_seed}</td>
                  <td className="col-status">
                    <span className={`eligibility-badge ${badge.cls}`} title={badge.label}>
                      {badge.icon}
                    </span>
                  </td>
                  <td className="col-stat col-ml" style={{ color: player.ml_probability >= 50 ? 'var(--success)' : player.ml_probability >= 20 ? 'var(--gold)' : 'var(--text-muted)' }}>
                    {player.ml_probability}%
                  </td>
                  <td className="col-score">
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
        <p className="model-blend">Final score = <strong>60% Heuristic Model</strong> (hand-tuned weights below) + <strong>40% ML Model</strong> (Gradient Boosting trained on 100 MVP candidates, 2005-2024)</p>

        <h4>Heuristic Model Weights (60% of final score)</h4>
        <div className="legend-grid">
          <div className="legend-item">
            <span className="legend-pct">15%</span>
            <strong>Team Success</strong> — Playoff seed + win% (top-3 seed won 19/20 MVPs)
          </div>
          <div className="legend-item">
            <span className="legend-pct">13%</span>
            <strong>Win Shares</strong> — Overall contribution to team wins (WS leader won 14/20 MVPs)
          </div>
          <div className="legend-item">
            <span className="legend-pct">13%</span>
            <strong>Scoring</strong> — Points per game vs. other candidates
          </div>
          <div className="legend-item">
            <span className="legend-pct">10%</span>
            <strong>📖 Narrative</strong> — Voter fatigue, fresh face bonus, triple-double milestones, scoring title, #1 seed narrative, historic efficiency
          </div>
          <div className="legend-item">
            <span className="legend-pct">10%</span>
            <strong>All-Around</strong> — Combined PTS+REB+AST (rewards triple-double types)
          </div>
          <div className="legend-item">
            <span className="legend-pct">10%</span>
            <strong>Advanced Stats</strong> — TS%, PIE, and Net Rating composite
          </div>
          <div className="legend-item">
            <span className="legend-pct">6%</span>
            <strong>Clutch</strong> — Performance in last 5 min of close games (&lt;5 pt margin)
          </div>
          <div className="legend-item">
            <span className="legend-pct">5%</span>
            <strong>Est. BPM</strong> — Estimated Box Plus/Minus (contribution above average)
          </div>
          <div className="legend-item">
            <span className="legend-pct">5%</span>
            <strong>Archetype Match</strong> — Similarity to historical MVP stat profiles
          </div>
          <div className="legend-item">
            <span className="legend-pct">5%</span>
            <strong>Defense</strong> — Steals, blocks, and defensive rating
          </div>
          <div className="legend-item">
            <span className="legend-pct">5%</span>
            <strong>Availability</strong> — Games played (65-game rule since 2023-24)
          </div>
          <div className="legend-item">
            <span className="legend-pct">3%</span>
            <strong>FG Efficiency</strong> — Field goal percentage
          </div>
        </div>

        <h4>ML Model Features (40% of final score)</h4>
        <p className="ml-description">Gradient Boosting classifier using 20 features: PPG, RPG, APG, STL, BLK, TS%, Win%, Seed, Win Shares, BPM, VORP, plus interaction features (PPG×Win%, WS/Seed, All-Around, Inverse Seed) and narrative features (triple-double avg, near triple-double, #1 seed, volume×efficiency, previous MVP). Trained on 100 historical candidates across 20 seasons.</p>

        <div className="eligibility-legend">
          <h4>Eligibility Status (65-Game Rule)</h4>
          <p>✅ Eligible — 65+ games played &nbsp;&nbsp; ⏳ Projected — On pace for 65 GP &nbsp;&nbsp; ❌ Ineligible — Won't reach 65 GP</p>
        </div>
      </div>
    </div>
  )
}
