"""Scraper for NBA player stats using nba_api (official NBA stats)."""

import time
from nba_api.stats.endpoints import leaguedashplayerstats, leaguedashplayerclutch
from scraper.cache import Cache, DiskCache

CURRENT_SEASON = 2026  # 2025-26 season

TEAM_ID_TO_NAME = {
    1610612737: "Atlanta Hawks", 1610612738: "Boston Celtics",
    1610612751: "Brooklyn Nets", 1610612766: "Charlotte Hornets",
    1610612741: "Chicago Bulls", 1610612739: "Cleveland Cavaliers",
    1610612742: "Dallas Mavericks", 1610612743: "Denver Nuggets",
    1610612765: "Detroit Pistons", 1610612744: "Golden State Warriors",
    1610612745: "Houston Rockets", 1610612754: "Indiana Pacers",
    1610612746: "Los Angeles Clippers", 1610612747: "Los Angeles Lakers",
    1610612763: "Memphis Grizzlies", 1610612748: "Miami Heat",
    1610612749: "Milwaukee Bucks", 1610612750: "Minnesota Timberwolves",
    1610612740: "New Orleans Pelicans", 1610612752: "New York Knicks",
    1610612760: "Oklahoma City Thunder", 1610612753: "Orlando Magic",
    1610612755: "Philadelphia 76ers", 1610612756: "Phoenix Suns",
    1610612757: "Portland Trail Blazers", 1610612758: "Sacramento Kings",
    1610612759: "San Antonio Spurs", 1610612761: "Toronto Raptors",
    1610612762: "Utah Jazz", 1610612764: "Washington Wizards",
}

TEAM_ID_TO_ABBREV = {
    1610612737: "ATL", 1610612738: "BOS", 1610612751: "BKN",
    1610612766: "CHA", 1610612741: "CHI", 1610612739: "CLE",
    1610612742: "DAL", 1610612743: "DEN", 1610612765: "DET",
    1610612744: "GSW", 1610612745: "HOU", 1610612754: "IND",
    1610612746: "LAC", 1610612747: "LAL", 1610612763: "MEM",
    1610612748: "MIA", 1610612749: "MIL", 1610612750: "MIN",
    1610612740: "NOP", 1610612752: "NYK", 1610612760: "OKC",
    1610612753: "ORL", 1610612755: "PHI", 1610612756: "PHX",
    1610612757: "POR", 1610612758: "SAC", 1610612759: "SAS",
    1610612761: "TOR", 1610612762: "UTA", 1610612764: "WAS",
}


def team_logo_url(team_id: int) -> str:
    return f"https://cdn.nba.com/logos/nba/{team_id}/primary/L/logo.svg"


def player_headshot_url(player_id: int) -> str:
    return f"https://cdn.nba.com/headshots/nba/latest/260x190/{player_id}.png"


class PlayersScraper:
    def __init__(self):
        self.cache = Cache(ttl_seconds=1800)
        self.disk = DiskCache()

    def _is_past_season(self, season_end_year: int) -> bool:
        return season_end_year < CURRENT_SEASON

    def _fetch_advanced_stats(self, season_end_year: int) -> dict:
        """Fetch advanced stats (PER, TS%, USG%, NET_RATING, etc.) keyed by player_id."""
        cache_key = f"player_advanced_{season_end_year}"

        if self._is_past_season(season_end_year):
            disk_data = self.disk.get(cache_key)
            if disk_data:
                return disk_data

        cached = self.cache.get(cache_key)
        if cached:
            return cached

        season_str = f"{season_end_year - 1}-{str(season_end_year)[-2:]}"
        time.sleep(0.6)

        adv = leaguedashplayerstats.LeagueDashPlayerStats(
            season=season_str,
            per_mode_detailed="PerGame",
            measure_type_detailed_defense="Advanced",
        )
        df = adv.get_data_frames()[0]

        result = {}
        for _, row in df.iterrows():
            pid = int(row.get("PLAYER_ID", 0))
            result[pid] = {
                "ts_pct": round(float(row.get("TS_PCT", 0)) * 100, 1),
                "usg_pct": round(float(row.get("USG_PCT", 0)) * 100, 1),
                "off_rating": round(float(row.get("OFF_RATING", 0)), 1),
                "def_rating": round(float(row.get("DEF_RATING", 0)), 1),
                "net_rating": round(float(row.get("NET_RATING", 0)), 1),
                "ast_pct": round(float(row.get("AST_PCT", 0)) * 100, 1),
                "reb_pct": round(float(row.get("REB_PCT", 0)) * 100, 1),
                "pie": round(float(row.get("PIE", 0)) * 100, 1),
                "pace": round(float(row.get("PACE", 0)), 1),
            }

        if self._is_past_season(season_end_year):
            self.disk.set(cache_key, result)
        self.cache.set(cache_key, result)
        return result

    def _fetch_clutch_stats(self, season_end_year: int) -> dict:
        """Fetch clutch stats (last 5 min, within 5 pts) keyed by player_id."""
        cache_key = f"player_clutch_{season_end_year}"

        if self._is_past_season(season_end_year):
            disk_data = self.disk.get(cache_key)
            if disk_data:
                return disk_data

        cached = self.cache.get(cache_key)
        if cached:
            return cached

        season_str = f"{season_end_year - 1}-{str(season_end_year)[-2:]}"
        time.sleep(0.6)

        try:
            clutch = leaguedashplayerclutch.LeagueDashPlayerClutch(
                season=season_str,
                per_mode_detailed="PerGame",
                clutch_time="Last 5 Minutes",
                ahead_behind="Ahead or Behind",
                point_diff=5,
            )
            df = clutch.get_data_frames()[0]

            result = {}
            for _, row in df.iterrows():
                pid = int(row.get("PLAYER_ID", 0))
                gp = int(row.get("GP", 0))
                if gp < 10:
                    continue
                result[pid] = {
                    "clutch_ppg": round(float(row.get("PTS", 0)), 1),
                    "clutch_fg_pct": round(float(row.get("FG_PCT", 0)) * 100, 1),
                    "clutch_plus_minus": round(float(row.get("PLUS_MINUS", 0)), 1),
                    "clutch_gp": gp,
                }

            if self._is_past_season(season_end_year):
                self.disk.set(cache_key, result)
            self.cache.set(cache_key, result)
            return result
        except Exception:
            return {}

    def get_season_totals(self, season_end_year: int = 2026) -> list[dict]:
        """Get all player season per-game stats from NBA API."""
        cache_key = f"player_totals_{season_end_year}"

        if self._is_past_season(season_end_year):
            disk_data = self.disk.get(cache_key)
            if disk_data:
                return disk_data

        cached = self.cache.get(cache_key)
        if cached:
            return cached

        season_str = f"{season_end_year - 1}-{str(season_end_year)[-2:]}"
        time.sleep(0.6)

        stats = leaguedashplayerstats.LeagueDashPlayerStats(
            season=season_str,
            per_mode_detailed="PerGame",
        )
        df = stats.get_data_frames()[0]

        # Fetch advanced and clutch stats
        advanced = self._fetch_advanced_stats(season_end_year)
        clutch = self._fetch_clutch_stats(season_end_year)

        players = []
        for _, row in df.iterrows():
            games = int(row.get("GP", 0))
            if games < 10:
                continue

            mpg = float(row.get("MIN", 0))
            ppg = float(row.get("PTS", 0))
            rpg = float(row.get("REB", 0))
            apg = float(row.get("AST", 0))
            spg = float(row.get("STL", 0))
            bpg = float(row.get("BLK", 0))
            tov = float(row.get("TOV", 0))
            fg_pct = float(row.get("FG_PCT", 0)) * 100
            ft_pct = float(row.get("FT_PCT", 0)) * 100
            fg3_pct = float(row.get("FG3_PCT", 0)) * 100
            fta = float(row.get("FTA", 0))
            fga = float(row.get("FGA", 0))

            team_id = int(row.get("TEAM_ID", 0))
            player_id = int(row.get("PLAYER_ID", 0))
            team_name = TEAM_ID_TO_NAME.get(team_id, str(row.get("TEAM_ABBREVIATION", "Unknown")))

            efficiency = round(ppg + rpg + apg + spg + bpg - tov, 1)
            ast_tov = round(apg / tov, 2) if tov > 0 else round(apg * 2, 2)
            ft_rate = round(fta / fga, 3) if fga > 0 else 0

            # Estimated PER (simplified Hollinger formula)
            # Uses per-game stats normalized to ~36 min, scaled to league average of 15
            min_factor = 36 / mpg if mpg > 0 else 1
            est_per = round((ppg + rpg * 1.2 + apg * 1.5 + spg * 2 + bpg * 2
                            - tov * 1.5 - (fga - fga * fg_pct/100) * 0.5) * min_factor * 0.9, 1)

            # Estimated BPM (simplified from Basketball-Reference methodology)
            # Positive = above average, uses key box score stats
            est_bpm = round(
                0.12 * ppg + 0.03 * rpg + 0.15 * apg + 0.35 * spg + 0.3 * bpg
                - 0.2 * tov - 3.5, 1
            )

            # Estimated VORP = (BPM - replacement_level) × (% of team min) × (team GP / 82)
            # Replacement level = -2.0
            pct_team_min = mpg / 48 if mpg > 0 else 0
            est_vorp = round((est_bpm - (-2.0)) * pct_team_min * (games / 82), 1)

            # Merge advanced stats
            adv = advanced.get(player_id, {})

            # Merge clutch stats
            cl = clutch.get(player_id, {})

            players.append({
                "name": row.get("PLAYER_NAME", "Unknown"),
                "player_id": player_id,
                "team": team_name,
                "team_id": team_id,
                "team_abbrev": TEAM_ID_TO_ABBREV.get(team_id, ""),
                "headshot_url": player_headshot_url(player_id),
                "team_logo_url": team_logo_url(team_id),
                "games": games,
                "ppg": round(ppg, 1),
                "rpg": round(rpg, 1),
                "apg": round(apg, 1),
                "spg": round(spg, 1),
                "bpg": round(bpg, 1),
                "tov_pg": round(tov, 1),
                "fg_pct": round(fg_pct, 1),
                "ft_pct": round(ft_pct, 1),
                "fg3_pct": round(fg3_pct, 1),
                "mpg": round(mpg, 1),
                "efficiency": efficiency,
                "ast_tov": ast_tov,
                "ft_rate": ft_rate,
                "est_per": est_per,
                "est_bpm": est_bpm,
                "est_vorp": est_vorp,
                # Advanced stats
                "ts_pct": adv.get("ts_pct", 0),
                "usg_pct": adv.get("usg_pct", 0),
                "off_rating": adv.get("off_rating", 0),
                "def_rating": adv.get("def_rating", 0),
                "net_rating": adv.get("net_rating", 0),
                "pie": adv.get("pie", 0),
                # Estimated Win Shares
                "est_ws": round(
                    (adv.get("pie", 0) / 100) * games * (mpg / 48) * 1.3, 1
                ) if adv.get("pie", 0) > 0 else 0,
                # Clutch stats
                "clutch_ppg": cl.get("clutch_ppg", 0),
                "clutch_fg_pct": cl.get("clutch_fg_pct", 0),
                "clutch_plus_minus": cl.get("clutch_plus_minus", 0),
            })

        if self._is_past_season(season_end_year):
            self.disk.set(cache_key, players)
        self.cache.set(cache_key, players)
        return players

    def get_top_players(self, season_end_year: int = 2026, limit: int = 25) -> list[dict]:
        """Get top MVP-candidate players.

        Uses the NBA 65-game rule: players need 65 games at 20+ min to be
        eligible for end-of-season awards. Players on pace to hit 65 are
        included and flagged as 'projected'.
        """
        players = self.get_season_totals(season_end_year)
        candidates = []
        for p in players:
            if p["mpg"] < 25 or p["ppg"] < 15:
                continue

            if p["games"] >= 65:
                status = "eligible"
            elif p["games"] >= 45:
                status = "projected"
            else:
                continue

            p["eligibility"] = status
            candidates.append(p)

        return sorted(candidates, key=lambda x: x["efficiency"], reverse=True)[:limit]
