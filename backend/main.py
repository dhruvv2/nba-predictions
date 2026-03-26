from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from predictions.game_predictor import GamePredictor
from predictions.mvp_predictor import MvpPredictor
from scraper.games import GamesScraper
from scraper.players import PlayersScraper
from scraper.mvp_history import MvpHistoryScraper

app = FastAPI(title="NBA Predictions API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

games_scraper = GamesScraper()
players_scraper = PlayersScraper()
mvp_history_scraper = MvpHistoryScraper()
game_predictor = GamePredictor(games_scraper)
mvp_predictor = MvpPredictor(players_scraper, mvp_history_scraper)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/predictions/games")
def get_game_predictions():
    """Get predictions for upcoming NBA games."""
    predictions = game_predictor.predict_upcoming_games()
    return {"predictions": predictions}


@app.get("/api/predictions/mvp")
def get_mvp_predictions():
    """Get current MVP race rankings."""
    rankings = mvp_predictor.predict_mvp_rankings()
    return {"rankings": rankings}


@app.get("/api/teams/standings")
def get_standings():
    """Get current team standings."""
    standings = games_scraper.get_standings()
    return {"standings": standings}


@app.get("/api/scores/live")
def get_live_scores():
    """Get today's live/recent scores."""
    from nba_api.stats.endpoints import scoreboardv2
    from datetime import datetime
    import time as _time

    today = datetime.now().strftime("%m/%d/%Y")
    _time.sleep(0.3)

    try:
        sb = scoreboardv2.ScoreboardV2(game_date=today)
        headers = sb.get_data_frames()[0]
        lines = sb.get_data_frames()[1]

        from scraper.games import TEAM_ID_TO_NAME
        from scraper.players import team_logo_url

        games = []
        for _, row in headers.iterrows():
            game_id = row.get("GAME_ID", "")
            home_id = int(row.get("HOME_TEAM_ID", 0))
            away_id = int(row.get("VISITOR_TEAM_ID", 0))
            status = str(row.get("GAME_STATUS_TEXT", ""))
            game_code = str(row.get("GAMECODE", ""))

            home_score = 0
            away_score = 0
            game_lines = lines[lines["GAME_ID"] == game_id]
            for _, ln in game_lines.iterrows():
                tid = int(ln.get("TEAM_ID", 0))
                pts = int(ln.get("PTS", 0) or 0)
                if tid == home_id:
                    home_score = pts
                elif tid == away_id:
                    away_score = pts

            games.append({
                "game_id": game_id,
                "status": status,
                "home_team": TEAM_ID_TO_NAME.get(home_id, "Unknown"),
                "away_team": TEAM_ID_TO_NAME.get(away_id, "Unknown"),
                "home_logo": team_logo_url(home_id),
                "away_logo": team_logo_url(away_id),
                "home_score": home_score,
                "away_score": away_score,
            })

        return {"games": games, "date": today}
    except Exception as e:
        return {"games": [], "date": today, "error": str(e)}
