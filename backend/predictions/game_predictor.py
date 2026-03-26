"""NBA game outcome prediction engine using heuristic/statistical approach."""

from scraper.players import team_logo_url

# Map team names to IDs for logo lookup
TEAM_NAME_TO_ID = {
    "Atlanta Hawks": 1610612737, "Boston Celtics": 1610612738,
    "Brooklyn Nets": 1610612751, "Charlotte Hornets": 1610612766,
    "Chicago Bulls": 1610612741, "Cleveland Cavaliers": 1610612739,
    "Dallas Mavericks": 1610612742, "Denver Nuggets": 1610612743,
    "Detroit Pistons": 1610612765, "Golden State Warriors": 1610612744,
    "Houston Rockets": 1610612745, "Indiana Pacers": 1610612754,
    "Los Angeles Clippers": 1610612746, "Los Angeles Lakers": 1610612747,
    "Memphis Grizzlies": 1610612763, "Miami Heat": 1610612748,
    "Milwaukee Bucks": 1610612749, "Minnesota Timberwolves": 1610612750,
    "New Orleans Pelicans": 1610612740, "New York Knicks": 1610612752,
    "Oklahoma City Thunder": 1610612760, "Orlando Magic": 1610612753,
    "Philadelphia 76ers": 1610612755, "Phoenix Suns": 1610612756,
    "Portland Trail Blazers": 1610612757, "Sacramento Kings": 1610612758,
    "San Antonio Spurs": 1610612759, "Toronto Raptors": 1610612761,
    "Utah Jazz": 1610612762, "Washington Wizards": 1610612764,
}


class GamePredictor:
    # Weights for team strength score components
    WEIGHTS = {
        "win_pct": 0.35,
        "point_diff": 0.25,
        "recent_form": 0.20,
        "home_away": 0.10,
        "head_to_head": 0.10,
    }
    HOME_COURT_BOOST = 0.03  # ~3% boost for home team

    def __init__(self, games_scraper):
        self.games_scraper = games_scraper

    def _team_strength(self, record: dict, is_home: bool) -> float:
        """Calculate a 0-1 team strength score."""
        win_pct = record.get("win_pct", 0.5)

        # Normalize point diff to 0-1 range (typical range: -10 to +10)
        raw_diff = record.get("point_diff", 0)
        norm_diff = max(0, min(1, (raw_diff + 15) / 30))

        recent = record.get("last_10_win_pct", 0.5)

        if is_home:
            home_away_pct = record.get("home_wins", 0) / max(1, record.get("home_wins", 0) + record.get("home_losses", 0))
        else:
            home_away_pct = record.get("away_wins", 0) / max(1, record.get("away_wins", 0) + record.get("away_losses", 0))

        strength = (
            self.WEIGHTS["win_pct"] * win_pct
            + self.WEIGHTS["point_diff"] * norm_diff
            + self.WEIGHTS["recent_form"] * recent
            + self.WEIGHTS["home_away"] * home_away_pct
        )

        if is_home:
            strength += self.HOME_COURT_BOOST

        return strength

    def predict_game(self, home_team: str, away_team: str) -> dict:
        """Predict the outcome of a single game."""
        records = self.games_scraper.get_team_records()
        h2h = self.games_scraper.get_head_to_head(home_team, away_team)

        home_record = records.get(home_team, {})
        away_record = records.get(away_team, {})

        home_strength = self._team_strength(home_record, is_home=True)
        away_strength = self._team_strength(away_record, is_home=False)

        # Add head-to-head factor
        h2h_total = h2h["team1_wins"] + h2h["team2_wins"]
        if h2h_total > 0:
            home_h2h = h2h["team1_wins"] / h2h_total if h2h["team1"] == home_team else h2h["team2_wins"] / h2h_total
            away_h2h = 1 - home_h2h
        else:
            home_h2h = 0.5
            away_h2h = 0.5

        home_strength += self.WEIGHTS["head_to_head"] * home_h2h
        away_strength += self.WEIGHTS["head_to_head"] * away_h2h

        # Convert to win probability
        total = home_strength + away_strength
        if total == 0:
            home_prob = 0.5
        else:
            home_prob = home_strength / total

        home_prob = max(0.15, min(0.85, home_prob))  # Clamp to reasonable range

        predicted_winner = home_team if home_prob >= 0.5 else away_team
        confidence = max(home_prob, 1 - home_prob) * 100

        return {
            "home_team": home_team,
            "away_team": away_team,
            "home_logo": team_logo_url(TEAM_NAME_TO_ID.get(home_team, 0)),
            "away_logo": team_logo_url(TEAM_NAME_TO_ID.get(away_team, 0)),
            "predicted_winner": predicted_winner,
            "confidence": round(confidence, 1),
            "home_win_prob": round(home_prob * 100, 1),
            "away_win_prob": round((1 - home_prob) * 100, 1),
            "home_season_record": f"{home_record.get('wins', 0)}-{home_record.get('losses', 0)}",
            "away_season_record": f"{away_record.get('wins', 0)}-{away_record.get('losses', 0)}",
            "home_point_diff": round(home_record.get("point_diff", 0), 1),
            "away_point_diff": round(away_record.get("point_diff", 0), 1),
            "factors": {
                "home_strength": round(home_strength, 3),
                "away_strength": round(away_strength, 3),
                "home_win_probability": round(home_prob * 100, 1),
                "home_court_advantage": True,
                "head_to_head": f"{h2h['team1_wins']}-{h2h['team2_wins']}",
                "home_recent_form": f"{int(home_record.get('last_10_win_pct', 0) * 10)}-{10 - int(home_record.get('last_10_win_pct', 0) * 10)} (L10)",
                "away_recent_form": f"{int(away_record.get('last_10_win_pct', 0) * 10)}-{10 - int(away_record.get('last_10_win_pct', 0) * 10)} (L10)",
            },
        }

    def predict_upcoming_games(self) -> list[dict]:
        """Predict outcomes for upcoming games."""
        upcoming = self.games_scraper.get_upcoming_games()
        predictions = []

        for game in upcoming:
            try:
                pred = self.predict_game(game["home_team"], game["away_team"])
                pred["date"] = game["date"]
                predictions.append(pred)
            except Exception:
                continue

        return predictions
