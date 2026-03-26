"""Scraper for NBA team stats, schedules, and standings using nba_api."""

import time
from datetime import datetime
from nba_api.stats.endpoints import leaguestandings, scoreboardv2, leaguegamefinder
from scraper.cache import Cache, DiskCache

CURRENT_SEASON = 2025  # Update this each new season

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


class GamesScraper:
    def __init__(self):
        self.cache = Cache(ttl_seconds=1800)
        self.disk = DiskCache()

    def _is_past_season(self, season_end_year: int) -> bool:
        return season_end_year < CURRENT_SEASON

    def get_team_records(self, season_end_year: int = 2025) -> dict[str, dict]:
        """Get team records from the NBA standings API."""
        cache_key = f"team_records_{season_end_year}"

        if self._is_past_season(season_end_year):
            disk_data = self.disk.get(cache_key)
            if disk_data:
                return disk_data

        cached = self.cache.get(cache_key)
        if cached:
            return cached

        season_str = f"{season_end_year - 1}-{str(season_end_year)[-2:]}"
        time.sleep(0.6)

        standings = leaguestandings.LeagueStandings(
            season=season_str,
            season_type="Regular Season",
        )
        df = standings.get_data_frames()[0]

        records = {}
        for _, row in df.iterrows():
            team_id = int(row.get("TeamID", 0))
            team_name = TEAM_ID_TO_NAME.get(team_id, str(row.get("TeamCity", "")) + " " + str(row.get("TeamName", "")))
            wins = int(row.get("WINS", 0))
            losses = int(row.get("LOSSES", 0))

            home_record = str(row.get("HOME", "0-0")).split("-")
            away_record = str(row.get("ROAD", "0-0")).split("-")
            l10_record = str(row.get("L10", "0-0")).split("-")

            home_wins = int(home_record[0]) if len(home_record) == 2 else 0
            home_losses = int(home_record[1]) if len(home_record) == 2 else 0
            away_wins = int(away_record[0]) if len(away_record) == 2 else 0
            away_losses = int(away_record[1]) if len(away_record) == 2 else 0
            l10_wins = int(l10_record[0]) if len(l10_record) == 2 else 0
            l10_total = l10_wins + (int(l10_record[1]) if len(l10_record) == 2 else 0)

            records[team_name] = {
                "team": team_name,
                "team_id": team_id,
                "wins": wins,
                "losses": losses,
                "win_pct": float(row.get("WinPCT", 0)),
                "home_wins": home_wins,
                "home_losses": home_losses,
                "away_wins": away_wins,
                "away_losses": away_losses,
                "point_diff": float(row.get("DiffPointsPG", 0)) if "DiffPointsPG" in row.index else 0,
                "points_for": float(row.get("PointsPG", 0)) if "PointsPG" in row.index else 0,
                "last_10_win_pct": l10_wins / l10_total if l10_total > 0 else 0.5,
                "last_10_results": [1] * l10_wins + [0] * (l10_total - l10_wins),
                "conference": str(row.get("Conference", "")),
                "conf_rank": int(row.get("PlayoffRank", 0)),
            }

        if self._is_past_season(season_end_year):
            self.disk.set(cache_key, records)
        self.cache.set(cache_key, records)
        return records

    def get_season_games(self, season_end_year: int = 2025) -> list[dict]:
        """Get all games played this season."""
        cache_key = f"season_games_{season_end_year}"

        if self._is_past_season(season_end_year):
            disk_data = self.disk.get(cache_key)
            if disk_data:
                return disk_data

        cached = self.cache.get(cache_key)
        if cached:
            return cached

        season_str = f"{season_end_year - 1}-{str(season_end_year)[-2:]}"
        time.sleep(0.6)

        finder = leaguegamefinder.LeagueGameFinder(
            season_nullable=season_str,
            season_type_nullable="Regular Season",
            league_id_nullable="00",
        )
        df = finder.get_data_frames()[0]

        game_map = {}
        for _, row in df.iterrows():
            gid = row.get("GAME_ID", "")
            matchup = str(row.get("MATCHUP", ""))
            team_name = row.get("TEAM_NAME", "")
            team_id = int(row.get("TEAM_ID", 0))
            full_name = TEAM_ID_TO_NAME.get(team_id, team_name)
            pts = int(row.get("PTS", 0))
            game_date = str(row.get("GAME_DATE", ""))[:10]

            if gid not in game_map:
                game_map[gid] = {"date": game_date}

            if " vs. " in matchup:
                game_map[gid]["home_team"] = full_name
                game_map[gid]["home_team_score"] = pts
            elif " @ " in matchup:
                game_map[gid]["away_team"] = full_name
                game_map[gid]["away_team_score"] = pts

        games = [g for g in game_map.values() if "home_team" in g and "away_team" in g]
        games.sort(key=lambda x: x["date"])

        if self._is_past_season(season_end_year):
            self.disk.set(cache_key, games)
        self.cache.set(cache_key, games)
        return games

    def get_upcoming_games(self, season_end_year: int = 2025) -> list[dict]:
        """Get upcoming games from today's scoreboard."""
        cache_key = "upcoming_games"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        today = datetime.now().strftime("%m/%d/%Y")
        time.sleep(0.6)

        try:
            sb = scoreboardv2.ScoreboardV2(game_date=today)
            header_df = sb.get_data_frames()[0]

            games = []
            for _, row in header_df.iterrows():
                home_id = int(row.get("HOME_TEAM_ID", 0))
                away_id = int(row.get("VISITOR_TEAM_ID", 0))
                game_date = str(row.get("GAME_DATE_EST", ""))[:10]

                games.append({
                    "date": game_date,
                    "home_team": TEAM_ID_TO_NAME.get(home_id, "Unknown"),
                    "away_team": TEAM_ID_TO_NAME.get(away_id, "Unknown"),
                    "home_team_score": None,
                    "away_team_score": None,
                })

            self.cache.set(cache_key, games)
            return games[:20]
        except Exception:
            return []

    def get_head_to_head(self, team1: str, team2: str, season_end_year: int = 2025) -> dict:
        """Get head-to-head record between two teams this season."""
        games = self.get_season_games(season_end_year)
        t1_wins, t2_wins = 0, 0

        for game in games:
            teams = {game.get("home_team"), game.get("away_team")}
            if team1 in teams and team2 in teams:
                home_score = game.get("home_team_score", 0) or 0
                away_score = game.get("away_team_score", 0) or 0
                if home_score == 0 and away_score == 0:
                    continue
                winner = game["home_team"] if home_score > away_score else game["away_team"]
                if winner == team1:
                    t1_wins += 1
                else:
                    t2_wins += 1

        return {"team1": team1, "team2": team2, "team1_wins": t1_wins, "team2_wins": t2_wins}

    def get_standings(self, season_end_year: int = 2025) -> list[dict]:
        """Get sorted standings."""
        records = self.get_team_records(season_end_year)
        standings = sorted(records.values(), key=lambda x: x["win_pct"], reverse=True)
        for i, team in enumerate(standings):
            team["rank"] = i + 1
        return standings
