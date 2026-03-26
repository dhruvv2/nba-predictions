"""NBA MVP prediction engine using historical archetype comparison and advanced stats.

Uses the NBA 65-game rule for eligibility and weights that align with
historical MVP voting patterns (scoring, team success, all-around play,
advanced efficiency metrics).
"""


class MvpPredictor:
    """Predicts MVP rankings using a weighted composite model with advanced stats.

    Key insight from historical data: MVPs almost always come from
    top-3 seeds, lead in scoring/efficiency, and play most games.
    Advanced stats (TS%, PIE, NET_RATING) separate truly elite from volume scorers.
    """

    WEIGHTS = {
        "scoring": 0.18,          # Raw PPG — voters love scorers
        "all_around": 0.17,       # Combined PTS+REB+AST impact
        "team_success": 0.18,     # Seed + win% — must be on a great team
        "advanced": 0.15,         # TS%, PIE, NET_RATING — true efficiency
        "archetype_match": 0.10,  # Similarity to past MVP stat profiles
        "defense": 0.07,          # STL, BLK, DEF_RATING — two-way impact
        "availability": 0.08,     # Games played — 65-game rule era
        "efficiency": 0.07,       # FG% — basic shooting efficiency
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

    def _advanced_score(self, player: dict, all_players: list[dict]) -> float:
        """Composite advanced stat score from TS%, PIE, and NET_RATING."""
        ts_vals = [p.get("ts_pct", 50) for p in all_players]
        pie_vals = [p.get("pie", 10) for p in all_players]
        net_vals = [p.get("net_rating", 0) for p in all_players]

        ts = self._normalize(player.get("ts_pct", 50), min(ts_vals), max(ts_vals))
        pie = self._normalize(player.get("pie", 10), min(pie_vals), max(pie_vals))
        net = self._normalize(player.get("net_rating", 0), min(net_vals), max(net_vals))

        return 0.35 * ts + 0.40 * pie + 0.25 * net

    def _defense_score(self, player: dict, all_players: list[dict]) -> float:
        """Composite defensive score from STL, BLK, and DEF_RATING."""
        stl_vals = [p.get("spg", 0) for p in all_players]
        blk_vals = [p.get("bpg", 0) for p in all_players]
        drtg_vals = [p.get("def_rating", 110) for p in all_players]

        stl = self._normalize(player.get("spg", 0), min(stl_vals), max(stl_vals))
        blk = self._normalize(player.get("bpg", 0), min(blk_vals), max(blk_vals))
        # Lower DEF_RATING is better — invert
        drtg = 1 - self._normalize(player.get("def_rating", 110), min(drtg_vals), max(drtg_vals))

        return 0.30 * stl + 0.30 * blk + 0.40 * drtg

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

        ppg_vals = [p["ppg"] for p in top_players]

        candidates = []
        for player in top_players:
            team_info = team_records.get(player["team"], {})
            team_win_pct = team_info.get("win_pct", 0.5)
            team_seed = team_info.get("rank", 15)

            # --- Component scores ---
            scoring = self._normalize(player["ppg"], min(ppg_vals), max(ppg_vals))

            all_around_val = player["ppg"] + player["rpg"] + player["apg"]
            all_around_vals = [p["ppg"] + p["rpg"] + p["apg"] for p in top_players]
            all_around = self._normalize(all_around_val, min(all_around_vals), max(all_around_vals))

            seed_score = max(0.1, 1.0 - (team_seed - 1) * 0.065)
            team_score = seed_score * min(1.0, team_win_pct / 0.55)

            adv_score = self._advanced_score(player, top_players)

            def_score = self._defense_score(player, top_players)

            arch_sim = self._archetype_similarity(player, team_win_pct, team_seed, archetype)

            gp_score = min(1, player["games"] / 72)

            fg_pct = player.get("fg_pct", 45)
            eff_score = self._normalize(fg_pct, 40, 65)

            # --- Bonuses ---
            prev_mvp_bonus = 0
            recent_mvps = [m["player"] for m in mvp_history[:5]]
            if player["name"] in recent_mvps:
                prev_mvp_bonus = 0.02

            dominant_bonus = 0
            if player["rpg"] >= 10 and player["apg"] >= 8:
                dominant_bonus = 0.06
            elif player["rpg"] >= 8 and player["apg"] >= 6:
                dominant_bonus = 0.03

            eligibility = player.get("eligibility", "projected")
            eligibility_mult = 1.0 if eligibility == "eligible" else 0.93

            mvp_score = (
                self.WEIGHTS["scoring"] * scoring
                + self.WEIGHTS["all_around"] * all_around
                + self.WEIGHTS["team_success"] * team_score
                + self.WEIGHTS["advanced"] * adv_score
                + self.WEIGHTS["defense"] * def_score
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
                "spg": player.get("spg", 0),
                "bpg": player.get("bpg", 0),
                "efficiency": player["efficiency"],
                "games": player["games"],
                "fg_pct": player.get("fg_pct", 0),
                "ts_pct": player.get("ts_pct", 0),
                "usg_pct": player.get("usg_pct", 0),
                "net_rating": player.get("net_rating", 0),
                "def_rating": player.get("def_rating", 0),
                "pie": player.get("pie", 0),
                "team_win_pct": round(team_win_pct * 100, 1),
                "team_seed": team_seed,
                "archetype_similarity": round(arch_sim * 100, 1),
                "eligibility": eligibility,
                "factors": {
                    "scoring": round(scoring * 100, 1),
                    "all_around": round(all_around * 100, 1),
                    "team_success": round(team_score * 100, 1),
                    "advanced": round(adv_score * 100, 1),
                    "defense": round(def_score * 100, 1),
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
