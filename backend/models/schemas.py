"""Pydantic models for API responses."""

from pydantic import BaseModel


class GamePrediction(BaseModel):
    date: str
    home_team: str
    home_team_abbrev: str
    away_team: str
    away_team_abbrev: str
    predicted_winner: str
    confidence: float
    home_win_pct: float
    away_win_pct: float
    home_point_diff: float
    away_point_diff: float
    factors: dict


class MvpCandidate(BaseModel):
    rank: int
    name: str
    team: str
    mvp_score: float
    ppg: float
    rpg: float
    apg: float
    efficiency: float
    team_win_pct: float
    archetype_similarity: float
    factors: dict


class HealthResponse(BaseModel):
    status: str
