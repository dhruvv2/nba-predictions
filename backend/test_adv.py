from scraper.players import PlayersScraper
from scraper.mvp_history import MvpHistoryScraper
from predictions.mvp_predictor import MvpPredictor

ps = PlayersScraper()
mh = MvpHistoryScraper()
mp = MvpPredictor(ps, mh)

rankings = mp.predict_mvp_rankings(2026)
for r in rankings[:10]:
    e = "OK" if r["eligibility"] == "eligible" else "PR"
    print(f'{r["rank"]:2}. [{e}] {r["name"]:25} Score:{r["mvp_score"]:5.1f} TS:{r["ts_pct"]}% PIE:{r["pie"]} NET:{r["net_rating"]:+.1f} Seed:{r["team_seed"]:2}')
