"""NBA MVP prediction engine using historical archetype comparison."""


class MvpPredictor:
    # Weights for MVP score components
    WEIGHTS = {
        "scoring": 0.25,
        "rebounds": 0.10,
        "assists": 0.15,
        "efficiency": 0.15,
        "team_success": 0.20,
        "archetype_match": 0.15,
    }

    def __init__(self, players_scraper, mvp_history_scraper):
        self.players_scraper = players_scraper
        self.mvp_history_scraper = mvp_history_scraper

    def _normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize a value to 0-1 range."""
        if max_val == min_val:
            return 0.5
        return max(0, min(1, (value - min_val) / (max_val - min_val)))

    def _archetype_similarity(self, player: dict, team_win_pct: float, team_seed: int, archetype: dict) -> float:
        """Calculate how closely a player matches the historical MVP archetype (0-1)."""
        ppg_diff = abs(player["ppg"] - archetype["avg_ppg"])
        rpg_diff = abs(player["rpg"] - archetype["avg_rpg"])
        apg_diff = abs(player["apg"] - archetype["avg_apg"])
        win_diff = abs(team_win_pct - archetype["avg_win_pct"])
        seed_diff = abs(team_seed - archetype["avg_seed"])

        # Convert differences to similarity scores (smaller diff = higher score)
        ppg_sim = max(0, 1 - ppg_diff / 15)
        rpg_sim = max(0, 1 - rpg_diff / 8)
        apg_sim = max(0, 1 - apg_diff / 6)
        win_sim = max(0, 1 - win_diff / 0.3)
        seed_sim = max(0, 1 - seed_diff / 8)

        return round(
            0.30 * ppg_sim + 0.10 * rpg_sim + 0.15 * apg_sim + 0.25 * win_sim + 0.20 * seed_sim,
            3,
        )

    def predict_mvp_rankings(self, season_end_year: int = 2025) -> list[dict]:
        """Predict MVP rankings for the current season."""
        from scraper.games import GamesScraper

        # Get data
        top_players = self.players_scraper.get_top_players(season_end_year, limit=30)
        archetype = self.mvp_history_scraper.get_mvp_archetype()
        mvp_history = self.mvp_history_scraper.get_mvp_history()

        # We need team records for team success factor
        games_scraper = GamesScraper()
        standings = games_scraper.get_standings(season_end_year)
        team_records = {t["team"]: t for t in standings}

        if not top_players:
            return []

        # Get ranges for normalization
        ppg_vals = [p["ppg"] for p in top_players]
        rpg_vals = [p["rpg"] for p in top_players]
        apg_vals = [p["apg"] for p in top_players]
        eff_vals = [p["efficiency"] for p in top_players]

        candidates = []
        for player in top_players:
            team_info = team_records.get(player["team"], {})
            team_win_pct = team_info.get("win_pct", 0.5)
            team_seed = team_info.get("rank", 15)

            # Compute component scores
            scoring_score = self._normalize(player["ppg"], min(ppg_vals), max(ppg_vals))
            rebound_score = self._normalize(player["rpg"], min(rpg_vals), max(rpg_vals))
            assist_score = self._normalize(player["apg"], min(apg_vals), max(apg_vals))
            efficiency_score = self._normalize(player["efficiency"], min(eff_vals), max(eff_vals))

            # Team success: heavily favor top seeds
            team_score = max(0, 1 - (team_seed - 1) / 14) * team_win_pct / 0.8
            team_score = min(1, team_score)

            # Archetype similarity
            arch_sim = self._archetype_similarity(player, team_win_pct, team_seed, archetype)

            # Previous MVP bonus — past winners who maintain elite play get a slight edge
            prev_mvp_bonus = 0
            recent_mvps = [m["player"] for m in mvp_history[:5]]
            if player["name"] in recent_mvps:
                prev_mvp_bonus = 0.03

            mvp_score = (
                self.WEIGHTS["scoring"] * scoring_score
                + self.WEIGHTS["rebounds"] * rebound_score
                + self.WEIGHTS["assists"] * assist_score
                + self.WEIGHTS["efficiency"] * efficiency_score
                + self.WEIGHTS["team_success"] * team_score
                + self.WEIGHTS["archetype_match"] * arch_sim
                + prev_mvp_bonus
            )

            candidates.append({
                "name": player["name"],
                "team": player["team"],
                "mvp_score": round(mvp_score * 100, 1),
                "ppg": player["ppg"],
                "rpg": player["rpg"],
                "apg": player["apg"],
                "efficiency": player["efficiency"],
                "team_win_pct": round(team_win_pct * 100, 1),
                "team_seed": team_seed,
                "archetype_similarity": round(arch_sim * 100, 1),
                "factors": {
                    "scoring": round(scoring_score * 100, 1),
                    "rebounds": round(rebound_score * 100, 1),
                    "assists": round(assist_score * 100, 1),
                    "efficiency": round(efficiency_score * 100, 1),
                    "team_success": round(team_score * 100, 1),
                    "archetype_match": round(arch_sim * 100, 1),
                    "previous_mvp_bonus": prev_mvp_bonus > 0,
                },
            })

        # Sort by MVP score descending
        candidates.sort(key=lambda x: x["mvp_score"], reverse=True)

        # Add rank
        for i, c in enumerate(candidates):
            c["rank"] = i + 1

        return candidates[:15]
