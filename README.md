# NBA Predictions

A website that predicts NBA game outcomes and MVP race standings using data from basketball-reference.com.

## Features

- **Game Predictions** — Heuristic model using team win%, point differential, recent form, home/away splits, and head-to-head records to predict winners with confidence percentages
- **MVP Race Rankings** — Composite scoring model that compares current players against a historical MVP archetype built from 20 years of past winners

## Tech Stack

- **Backend**: Python + FastAPI
- **Frontend**: React (Vite)
- **Data Source**: basketball-reference.com (via `basketball_reference_web_scraper`)

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Health check |
| `GET /api/predictions/games` | Game predictions for upcoming games |
| `GET /api/predictions/mvp` | MVP race rankings |
| `GET /api/teams/standings` | Current team standings |

## How Predictions Work

### Game Predictions
Team strength is computed from weighted factors:
- **Win %** (35%) — Overall season record
- **Point Differential** (25%) — Average margin of victory/defeat
- **Recent Form** (20%) — Last 10 games record
- **Home/Away** (10%) — Performance at home vs on the road
- **Head-to-Head** (10%) — Season series record
- **Home Court Advantage** — ~3% boost for the home team

### MVP Predictions
Players are scored using:
- **Scoring** (25%) — PPG relative to other candidates
- **Team Success** (20%) — Team seed and win percentage
- **Assists** (15%) — Playmaking contribution
- **Efficiency** (15%) — Overall stat efficiency
- **Archetype Match** (15%) — Similarity to historical MVP stat profiles (last 20 winners)
- **Rebounds** (10%) — Rebounding contribution
- **Previous MVP Bonus** — Small edge for recent MVP winners maintaining elite play

## License

MIT
