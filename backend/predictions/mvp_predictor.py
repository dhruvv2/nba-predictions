"""NBA MVP prediction engine using historical archetype comparison and advanced stats,
blended with a gradient boosting ML model trained on 2005-2024 MVP races.

The final MVP score is a weighted blend:
  60% heuristic model (hand-tuned weights calibrated to voting patterns)
  40% ML model (gradient boosting trained on historical candidate data)

This dual approach leverages the interpretability of the heuristic model
with the pattern-recognition power of the ML model.
"""

from predictions.ml_mvp_model import MlMvpModel


class MvpPredictor:
    """Predicts MVP rankings using a weighted composite model.

    Weights are calibrated to match historical MVP voting patterns.
    Win Shares is the strongest single predictor, followed by team
    success and scoring volume.
    """

    # Weights sum to ~1.0, calibrated to historical MVP voting
    WEIGHTS = {
        "win_shares": 0.13,       # Strongest single MVP predictor historically
        "team_success": 0.15,     # Top-3 seed won 19/20 times (2005-2024)
        "scoring": 0.13,          # PPG - scoring leaders win ~40% of MVPs
        "narrative": 0.10,        # Voter fatigue, fresh face, milestones
        "all_around": 0.10,       # PTS+REB+AST - triple-double era bonus
        "advanced": 0.10,         # TS%, PIE, NET_RATING - efficiency
        "clutch": 0.06,           # Clutch PPG + FG% + +/- in close games
        "est_bpm": 0.05,          # Estimated Box Plus/Minus
        "archetype_match": 0.05,  # Similarity to past MVP stat profiles
        "defense": 0.05,          # STL, BLK, DEF_RATING - two-way impact
        "availability": 0.05,     # Games played - 65-game rule era
        "efficiency": 0.03,       # FG% - basic shooting efficiency
    }

    def __init__(self, players_scraper, mvp_history_scraper):
        self.players_scraper = players_scraper
        self.mvp_history_scraper = mvp_history_scraper
        self.ml_model = MlMvpModel()

    def _normalize(self, value, min_val, max_val):
        if max_val == min_val:
            return 0.5
        return max(0, min(1, (value - min_val) / (max_val - min_val)))

    def _archetype_similarity(self, player, team_win_pct, team_seed, archetype):
        ppg_sim = max(0, 1 - abs(player["ppg"] - archetype["avg_ppg"]) / 15)
        rpg_sim = max(0, 1 - abs(player["rpg"] - archetype["avg_rpg"]) / 8)
        apg_sim = max(0, 1 - abs(player["apg"] - archetype["avg_apg"]) / 6)
        win_sim = max(0, 1 - abs(team_win_pct - archetype["avg_win_pct"]) / 0.3)
        seed_sim = max(0, 1 - abs(team_seed - archetype["avg_seed"]) / 8)
        return round(0.30*ppg_sim + 0.10*rpg_sim + 0.15*apg_sim + 0.25*win_sim + 0.20*seed_sim, 3)

    def _advanced_score(self, player, all_players):
        ts_vals = [p.get("ts_pct", 50) for p in all_players]
        pie_vals = [p.get("pie", 10) for p in all_players]
        net_vals = [p.get("net_rating", 0) for p in all_players]
        ts = self._normalize(player.get("ts_pct", 50), min(ts_vals), max(ts_vals))
        pie = self._normalize(player.get("pie", 10), min(pie_vals), max(pie_vals))
        net = self._normalize(player.get("net_rating", 0), min(net_vals), max(net_vals))
        return 0.35 * ts + 0.40 * pie + 0.25 * net

    def _defense_score(self, player, all_players):
        stl_vals = [p.get("spg", 0) for p in all_players]
        blk_vals = [p.get("bpg", 0) for p in all_players]
        drtg_vals = [p.get("def_rating", 110) for p in all_players]
        stl = self._normalize(player.get("spg", 0), min(stl_vals), max(stl_vals))
        blk = self._normalize(player.get("bpg", 0), min(blk_vals), max(blk_vals))
        drtg = 1 - self._normalize(player.get("def_rating", 110), min(drtg_vals), max(drtg_vals))
        return 0.30 * stl + 0.30 * blk + 0.40 * drtg

    def _narrative_score(self, player, team_seed, team_win_pct, all_players, mvp_history):
        """Score narrative factors that historically influence MVP voting.

        Captures the 'storyline' elements that pure stats miss:
        - Voter fatigue: voters tire of giving MVP to the same player
        - Fresh face bonus: new contenders generate excitement
        - Milestone seasons: triple-double averages, historic efficiency
        - Scoring title: leading the league in PPG carries weight
        - Best record: team with #1 seed gets extra narrative push
        """
        score = 0.5  # baseline

        # --- Voter fatigue / fresh face ---
        recent_winners = [m["player"] for m in mvp_history[:3]]
        all_winners = [m["player"] for m in mvp_history]

        if player["name"] not in all_winners:
            # Never won MVP — fresh face bonus (Rose 2011, Curry 2015, Giannis 2019)
            score += 0.15
        elif player["name"] == recent_winners[0]:
            # Won LAST year — strong voter fatigue penalty
            # (Only Jokic, LeBron, Giannis, Nash, Curry overcame this)
            score -= 0.18
        elif player["name"] in recent_winners[1:3]:
            # Won 2-3 years ago — mild fatigue
            score -= 0.06

        # Count consecutive MVPs — exponential fatigue
        consecutive = 0
        for m in mvp_history:
            if m["player"] == player["name"]:
                consecutive += 1
            else:
                break
        if consecutive >= 3:
            score -= 0.15  # Very rare to win 4+ (only Russell, Wilt, LeBron)
        elif consecutive >= 2:
            score -= 0.08  # Tough to three-peat

        # --- Triple-double milestone ---
        # Averaging a triple-double is historic (Westbrook 2017, Jokic 2021+)
        if player["rpg"] >= 10 and player["apg"] >= 10:
            score += 0.20  # True triple-double average
        elif player["rpg"] >= 10 and player["apg"] >= 8:
            score += 0.12  # Near triple-double (Jokic profile)
        elif player["rpg"] >= 8 and player["apg"] >= 8:
            score += 0.08  # Elite all-around

        # --- Scoring title ---
        max_ppg = max(p["ppg"] for p in all_players)
        if player["ppg"] >= max_ppg - 0.5:
            score += 0.10  # Scoring leader or within 0.5 PPG

        # --- Best record narrative ---
        if team_seed == 1:
            score += 0.10  # Best player on #1 seed is a powerful narrative
        elif team_seed == 2:
            score += 0.04

        # --- Historic efficiency ---
        # 65%+ TS on 25+ PPG is historically rare and generates buzz
        ts = player.get("ts_pct", 0)
        if ts >= 65 and player["ppg"] >= 25:
            score += 0.10
        elif ts >= 63 and player["ppg"] >= 28:
            score += 0.06

        # --- High-volume dominance ---
        # 30+ PPG is always a narrative (Harden 2018-19, Curry 2016)
        if player["ppg"] >= 32:
            score += 0.08
        elif player["ppg"] >= 30:
            score += 0.04

        return max(0, min(1, score))

    def predict_mvp_rankings(self, season_end_year=2026):
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
        ws_vals = [p.get("est_ws", 0) for p in top_players]

        candidates = []
        # First pass: compute heuristic scores and raw ML probabilities
        raw_results = []
        for player in top_players:
            team_info = team_records.get(player["team"], {})
            team_win_pct = team_info.get("win_pct", 0.5)
            team_seed = team_info.get("rank", 15)

            ws_score = self._normalize(player.get("est_ws", 0), min(ws_vals), max(ws_vals))
            scoring = self._normalize(player["ppg"], min(ppg_vals), max(ppg_vals))

            aa_val = player["ppg"] + player["rpg"] + player["apg"]
            aa_vals = [p["ppg"] + p["rpg"] + p["apg"] for p in top_players]
            all_around = self._normalize(aa_val, min(aa_vals), max(aa_vals))

            seed_score = max(0.1, 1.0 - (team_seed - 1) * 0.065)
            team_score = seed_score * min(1.0, team_win_pct / 0.55)

            adv_score = self._advanced_score(player, top_players)
            def_score = self._defense_score(player, top_players)
            arch_sim = self._archetype_similarity(player, team_win_pct, team_seed, archetype)
            gp_score = min(1, player["games"] / 72)
            eff_score = self._normalize(player.get("fg_pct", 45), 40, 65)

            clutch_ppg_vals = [p.get("clutch_ppg", 0) for p in top_players]
            clutch_pm_vals = [p.get("clutch_plus_minus", 0) for p in top_players]
            clutch_score = (
                0.50 * self._normalize(player.get("clutch_ppg", 0), min(clutch_ppg_vals), max(clutch_ppg_vals))
                + 0.20 * self._normalize(player.get("clutch_fg_pct", 40), 30, 60)
                + 0.30 * self._normalize(player.get("clutch_plus_minus", 0), min(clutch_pm_vals), max(clutch_pm_vals))
            )

            bpm_vals = [p.get("est_bpm", 0) for p in top_players]
            bpm_score = self._normalize(player.get("est_bpm", 0), min(bpm_vals), max(bpm_vals))

            narrative = self._narrative_score(player, team_seed, team_win_pct, top_players, mvp_history)

            eligibility = player.get("eligibility", "projected")
            eligibility_mult = 1.0 if eligibility == "eligible" else 0.93

            heuristic_score = (
                self.WEIGHTS["win_shares"] * ws_score
                + self.WEIGHTS["scoring"] * scoring
                + self.WEIGHTS["all_around"] * all_around
                + self.WEIGHTS["team_success"] * team_score
                + self.WEIGHTS["advanced"] * adv_score
                + self.WEIGHTS["narrative"] * narrative
                + self.WEIGHTS["clutch"] * clutch_score
                + self.WEIGHTS["est_bpm"] * bpm_score
                + self.WEIGHTS["defense"] * def_score
                + self.WEIGHTS["archetype_match"] * arch_sim
                + self.WEIGHTS["availability"] * gp_score
                + self.WEIGHTS["efficiency"] * eff_score
            ) * eligibility_mult

            raw_results.append({
                "player": player,
                "heuristic_score": heuristic_score,
                "team_win_pct": team_win_pct,
                "team_seed": team_seed,
                "eligibility": eligibility,
                "scores": {
                    "ws": ws_score, "scoring": scoring, "all_around": all_around,
                    "team": team_score, "adv": adv_score, "narrative": narrative,
                    "clutch": clutch_score, "bpm": bpm_score, "def": def_score,
                    "arch": arch_sim, "gp": gp_score, "eff": eff_score,
                },
            })

        # Batch ML prediction using decision function for smoother ranking
        last_mvp = mvp_history[0]["player"] if mvp_history else ""
        ml_inputs = [
            {
                **r["player"],
                "team_win_pct": round(r["team_win_pct"] * 100, 1),
                "team_seed": r["team_seed"],
                "is_prev_mvp": r["player"]["name"] == last_mvp,
            }
            for r in raw_results
        ]
        ml_results = self.ml_model.predict_mvp_scores(ml_inputs)

        for r, ml in zip(raw_results, ml_results):
            player = r["player"]
            s = r["scores"]

            # Blend: 60% heuristic, 40% ML (decision function normalized to 0-1)
            mvp_score = 0.60 * r["heuristic_score"] + 0.40 * ml["ml_score"]

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
                "est_ws": player.get("est_ws", 0),
                "ast_tov": player.get("ast_tov", 0),
                "ft_rate": player.get("ft_rate", 0),
                "est_per": player.get("est_per", 0),
                "est_bpm": player.get("est_bpm", 0),
                "est_vorp": player.get("est_vorp", 0),
                "clutch_ppg": player.get("clutch_ppg", 0),
                "clutch_fg_pct": player.get("clutch_fg_pct", 0),
                "clutch_plus_minus": player.get("clutch_plus_minus", 0),
                "team_win_pct": round(r["team_win_pct"] * 100, 1),
                "team_seed": r["team_seed"],
                "archetype_similarity": round(s["arch"] * 100, 1),
                "eligibility": r["eligibility"],
                "ml_probability": round(ml["ml_probability"] * 100, 1),
                "heuristic_score": round(r["heuristic_score"] * 100, 1),
                "factors": {
                    "win_shares": round(s["ws"] * 100, 1),
                    "scoring": round(s["scoring"] * 100, 1),
                    "all_around": round(s["all_around"] * 100, 1),
                    "team_success": round(s["team"] * 100, 1),
                    "advanced": round(s["adv"] * 100, 1),
                    "narrative": round(s["narrative"] * 100, 1),
                    "clutch": round(s["clutch"] * 100, 1),
                    "est_bpm": round(s["bpm"] * 100, 1),
                    "defense": round(s["def"] * 100, 1),
                    "archetype_match": round(s["arch"] * 100, 1),
                    "availability": round(s["gp"] * 100, 1),
                    "efficiency": round(s["eff"] * 100, 1),
                },
            })

        candidates.sort(key=lambda x: x["mvp_score"], reverse=True)
        for i, c in enumerate(candidates):
            c["rank"] = i + 1

        return candidates[:15]
