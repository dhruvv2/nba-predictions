"""NBA MVP prediction engine using historical archetype comparison.

Uses the NBA 65-game rule for eligibility and weights that align with
historical MVP voting patterns (scoring, team success, all-around play).
"""


class MvpPredictor:
    """Predicts MVP rankings using a weighted composite model.

    Key insight from historical data: MVPs almost always come from
    top-3 seeds, lead in scoring/efficiency, and play most games.
    The model weights reflect actual voter behavior patterns.
    """

    WEIGHTS = {
        "scoring": 0.25,          # Raw PPG — voters love scorers
        "all_around": 0.20,       # Combined PTS+REB+AST impact
        "team_success": 0.20,     # Seed + win% — must be on a great team
        "archetype_match": 0.15,  # Similarity to past MVP stat profiles
        "availability": 0.10,     # Games played — 65-game rule era
        "efficiency": 0.10,       # Shooting efficiency (FG%)
    }

    def __init__(self, players_scraper, mvp_history_scraper):
        self.players_scraper = players_scraper
        self.mvp_history_scraper = mvp_history_scraper

    def _normalize(self, value: float, min_val: float, max_val: float) -> float:
        if max_val == min_val:
            return 0.5
        return max(0, min(1, (value - min_val) / (max_val - min_val)))

    def _archetype_similarity(self, player: dict, team_win_pct: float, team_seed: int, archetype: dict) -> float:
        """How closely a player matches the historical MVP archetype (0-1)."""
        ppg_diff = abs(player["ppg"] - archetype["avg_ppg"])
        rpg_diff = abs(player["rpg"] - archetype["avg_rpg"])
        apg_diff = abs(player["apg"] - archetype["avg_apg"])
        win_diff = abs(team_win_pct - archetype["avg_win_pct"])
        seed_diff = abs(team_seed - archetype["avg_seed"])

        ppg_sim = max(0, 1 - ppg_diff / 15)
        rpg_sim = max(0, 1 - rpg_diff / 8)
        apg_sim = max(0, 1 - apg_diff / 6)
        win_sim = max(0, 1 - win_diff / 0.3)
        seed_sim = max(0, 1 - seed_diff / 8)

        return round(
            0.30 * ppg_sim + 0.10 * rpg_sim + 0.15 * apg_sim + 0.25 * win_sim + 0.20 * seed_sim,
            3,
        )

    def predict_mvp_rankings(self, season_end_year: int = 2026) -> list[dict]:
        """Predict MVP rankings for the current season."""
        from scraper.games import GamesScraper

        top_players = self.players_scraper.get_top_players(season_end_year, limit=30)
        archetype = self.mvp_history_scraper.get_mvp_archetype()
        mvp_history = self.mvp_history_scraper.get_mvp_history()

        games_scraper = GamesScraper()
        standings = games_scraper.get_standings(season_end_year)
        team_records = {t["team"]: t for t in standings}

        if not top_players:
            return []

        # Normalization ranges from candidates
        ppg_vals = [p["ppg"] for p in top_players]
        rpg_vals = [p["rpg"] for p in top_players]
        apg_vals = [p["apg"] for p in top_players]
        eff_vals = [p["efficiency"] for p in top_players]

        candidates = []
        for player in top_players:
            team_info = team_records.get(player["team"], {})
            team_win_pct = team_info.get("win_pct", 0.5)
            team_seed = team_info.get("rank", 15)

            # --- Component scores ---

            # Scoring: pure PPG normalized
            scoring = self._normalize(player["ppg"], min(ppg_vals), max(ppg_vals))

            # All-around: combined stat-stuffing (PTS + REB + AST per game)
            all_around_val = player["ppg"] + player["rpg"] + player["apg"]
            all_around_vals = [p["ppg"] + p["rpg"] + p["apg"] for p in top_players]
            all_around = self._normalize(all_around_val, min(all_around_vals), max(all_around_vals))

            # Team success: gradual decay by seed (voters care but not as steeply
            # as past models assumed — Jokić won MVP on a 6th seed in 2024).
            seed_score = max(0.1, 1.0 - (team_seed - 1) * 0.065)
            team_score = seed_score * min(1.0, team_win_pct / 0.55)

            # Archetype match
            arch_sim = self._archetype_similarity(player, team_win_pct, team_seed, archetype)

            # Availability: 65-game rule makes this critical
            gp_score = min(1, player["games"] / 72)

            # Efficiency: FG% as a proxy for scoring efficiency
            fg_pct = player.get("fg_pct", 45)
            eff_score = self._normalize(fg_pct, 40, 65)

            # --- Bonuses ---
            prev_mvp_bonus = 0
            recent_mvps = [m["player"] for m in mvp_history[:5]]
            if player["name"] in recent_mvps:
                prev_mvp_bonus = 0.02

            # Dominant all-around bonus: reward players near triple-double averages
            dominant_bonus = 0
            if player["rpg"] >= 10 and player["apg"] >= 8:
                dominant_bonus = 0.06  # Triple-double territory
            elif player["rpg"] >= 8 and player["apg"] >= 6:
                dominant_bonus = 0.03

            # Penalty for players unlikely to hit 65 games
            eligibility = player.get("eligibility", "projected")
            eligibility_mult = 1.0 if eligibility == "eligible" else 0.93

            mvp_score = (
                self.WEIGHTS["scoring"] * scoring
                + self.WEIGHTS["all_around"] * all_around
                + self.WEIGHTS["team_success"] * team_score
                + self.WEIGHTS["archetype_match"] * arch_sim
                + self.WEIGHTS["availability"] * gp_score
                + self.WEIGHTS["efficiency"] * eff_score
                + prev_mvp_bonus
                + dominant_bonus
            ) * eligibility_mult

            candidates.append({
                "name": player["name"],
                "team": player["team"],
                "headshot_url": player.get("headshot_url", ""),
                "team_logo_url": player.get("team_logo_url", ""),
                "mvp_score": round(mvp_score * 100, 1),
                "ppg": player["ppg"],
                "rpg": player["rpg"],
                "apg": player["apg"],
                "efficiency": player["efficiency"],
                "games": player["games"],
                "fg_pct": player.get("fg_pct", 0),
                "team_win_pct": round(team_win_pct * 100, 1),
                "team_seed": team_seed,
                "archetype_similarity": round(arch_sim * 100, 1),
                "eligibility": eligibility,
                "factors": {
                    "scoring": round(scoring * 100, 1),
                    "all_around": round(all_around * 100, 1),
                    "team_success": round(team_score * 100, 1),
                    "archetype_match": round(arch_sim * 100, 1),
                    "availability": round(gp_score * 100, 1),
                    "efficiency": round(eff_score * 100, 1),
                    "previous_mvp_bonus": prev_mvp_bonus > 0,
                },
            })

        candidates.sort(key=lambda x: x["mvp_score"], reverse=True)
        for i, c in enumerate(candidates):
            c["rank"] = i + 1

        return candidates[:15]
