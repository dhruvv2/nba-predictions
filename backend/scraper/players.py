"""Scraper for NBA player stats using nba_api (official NBA stats)."""

import time
from nba_api.stats.endpoints import leagueleaders
from scraper.cache import Cache

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


class PlayersScraper:
    def __init__(self):
        self.cache = Cache(ttl_seconds=1800)

    def get_season_totals(self, season_end_year: int = 2025) -> list[dict]:
        """Get player season per-game stats from NBA API."""
        cache_key = f"player_totals_{season_end_year}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        season_str = f"{season_end_year - 1}-{str(season_end_year)[-2:]}"
        time.sleep(0.6)

        leaders = leagueleaders.LeagueLeaders(
            season=season_str,
            season_type_all_star="Regular Season",
            per_mode48="PerGame",
        )
        df = leaders.get_data_frames()[0]

        players = []
        for _, row in df.iterrows():
            games = int(row.get("GP", 0))
            if games < 20:
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

            team_id = int(row.get("TEAM_ID", 0))
            team_name = TEAM_ID_TO_NAME.get(team_id, row.get("TEAM", "Unknown"))

            efficiency = round(ppg + rpg + apg + spg + bpg - tov, 1)

            players.append({
                "name": row.get("PLAYER", "Unknown"),
                "team": team_name,
                "team_id": team_id,
                "games": games,
                "ppg": round(ppg, 1),
                "rpg": round(rpg, 1),
                "apg": round(apg, 1),
                "spg": round(spg, 1),
                "bpg": round(bpg, 1),
                "tov_pg": round(tov, 1),
                "fg_pct": round(fg_pct, 1),
                "ft_pct": round(ft_pct, 1),
                "mpg": round(mpg, 1),
                "efficiency": efficiency,
            })

        self.cache.set(cache_key, players)
        return players

    def get_top_players(self, season_end_year: int = 2025, limit: int = 25) -> list[dict]:
        """Get top players by efficiency rating."""
        players = self.get_season_totals(season_end_year)
        starters = [p for p in players if p["mpg"] >= 25]
        return sorted(starters, key=lambda x: x["efficiency"], reverse=True)[:limit]
