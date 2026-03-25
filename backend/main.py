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
    allow_origins=["http://localhost:5173"],
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
