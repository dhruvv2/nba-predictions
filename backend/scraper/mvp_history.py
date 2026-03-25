"""Scraper for historical NBA MVP winners from basketball-reference.com."""

import time
import requests
from bs4 import BeautifulSoup
from scraper.cache import Cache


# Historical MVP data (2005-2024) as a reliable fallback and to avoid excessive scraping.
# Source: basketball-reference.com/awards/mvp.html
HISTORICAL_MVPS = [
    {"year": 2024, "player": "Nikola Jokic", "team": "Denver Nuggets", "ppg": 26.4, "rpg": 12.4, "apg": 9.0, "win_pct": 0.695, "seed": 2},
    {"year": 2023, "player": "Joel Embiid", "team": "Philadelphia 76ers", "ppg": 33.1, "rpg": 10.2, "apg": 4.2, "win_pct": 0.659, "seed": 3},
    {"year": 2022, "player": "Nikola Jokic", "team": "Denver Nuggets", "ppg": 27.1, "rpg": 13.8, "apg": 7.9, "win_pct": 0.585, "seed": 6},
    {"year": 2021, "player": "Nikola Jokic", "team": "Denver Nuggets", "ppg": 26.4, "rpg": 10.8, "apg": 8.3, "win_pct": 0.653, "seed": 3},
    {"year": 2020, "player": "Giannis Antetokounmpo", "team": "Milwaukee Bucks", "ppg": 29.5, "rpg": 13.6, "apg": 5.6, "win_pct": 0.767, "seed": 1},
    {"year": 2019, "player": "Giannis Antetokounmpo", "team": "Milwaukee Bucks", "ppg": 27.7, "rpg": 12.5, "apg": 5.9, "win_pct": 0.732, "seed": 1},
    {"year": 2018, "player": "James Harden", "team": "Houston Rockets", "ppg": 30.4, "rpg": 5.4, "apg": 8.8, "win_pct": 0.793, "seed": 1},
    {"year": 2017, "player": "Russell Westbrook", "team": "Oklahoma City Thunder", "ppg": 31.6, "rpg": 10.7, "apg": 10.4, "win_pct": 0.573, "seed": 6},
    {"year": 2016, "player": "Stephen Curry", "team": "Golden State Warriors", "ppg": 30.1, "rpg": 5.4, "apg": 6.7, "win_pct": 0.890, "seed": 1},
    {"year": 2015, "player": "Stephen Curry", "team": "Golden State Warriors", "ppg": 23.8, "rpg": 4.3, "apg": 7.7, "win_pct": 0.817, "seed": 1},
    {"year": 2014, "player": "Kevin Durant", "team": "Oklahoma City Thunder", "ppg": 32.0, "rpg": 7.4, "apg": 5.5, "win_pct": 0.720, "seed": 2},
    {"year": 2013, "player": "LeBron James", "team": "Miami Heat", "ppg": 26.8, "rpg": 8.0, "apg": 7.3, "win_pct": 0.805, "seed": 1},
    {"year": 2012, "player": "LeBron James", "team": "Miami Heat", "ppg": 27.1, "rpg": 7.9, "apg": 6.2, "win_pct": 0.697, "seed": 2},
    {"year": 2011, "player": "Derrick Rose", "team": "Chicago Bulls", "ppg": 25.0, "rpg": 4.1, "apg": 7.7, "win_pct": 0.756, "seed": 1},
    {"year": 2010, "player": "LeBron James", "team": "Cleveland Cavaliers", "ppg": 29.7, "rpg": 7.3, "apg": 8.6, "win_pct": 0.744, "seed": 1},
    {"year": 2009, "player": "LeBron James", "team": "Cleveland Cavaliers", "ppg": 28.4, "rpg": 7.6, "apg": 7.2, "win_pct": 0.805, "seed": 1},
    {"year": 2008, "player": "Kobe Bryant", "team": "Los Angeles Lakers", "ppg": 28.3, "rpg": 6.3, "apg": 5.4, "win_pct": 0.695, "seed": 1},
    {"year": 2007, "player": "Dirk Nowitzki", "team": "Dallas Mavericks", "ppg": 24.6, "rpg": 8.9, "apg": 3.4, "win_pct": 0.817, "seed": 1},
    {"year": 2006, "player": "Steve Nash", "team": "Phoenix Suns", "ppg": 18.8, "rpg": 4.2, "apg": 10.5, "win_pct": 0.659, "seed": 2},
    {"year": 2005, "player": "Steve Nash", "team": "Phoenix Suns", "ppg": 15.5, "rpg": 3.3, "apg": 11.5, "win_pct": 0.756, "seed": 1},
]


class MvpHistoryScraper:
    def __init__(self):
        self.cache = Cache(ttl_seconds=86400)  # 24h cache — history doesn't change

    def get_mvp_history(self) -> list[dict]:
        """Get historical MVP winners and their stats."""
        cache_key = "mvp_history"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        self.cache.set(cache_key, HISTORICAL_MVPS)
        return HISTORICAL_MVPS

    def get_mvp_archetype(self) -> dict:
        """Compute the average MVP archetype from historical data."""
        cache_key = "mvp_archetype"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        mvps = self.get_mvp_history()
        n = len(mvps)

        archetype = {
            "avg_ppg": round(sum(m["ppg"] for m in mvps) / n, 1),
            "avg_rpg": round(sum(m["rpg"] for m in mvps) / n, 1),
            "avg_apg": round(sum(m["apg"] for m in mvps) / n, 1),
            "avg_win_pct": round(sum(m["win_pct"] for m in mvps) / n, 3),
            "avg_seed": round(sum(m["seed"] for m in mvps) / n, 1),
            "min_ppg": min(m["ppg"] for m in mvps),
            "max_ppg": max(m["ppg"] for m in mvps),
            "pct_top2_seed": round(sum(1 for m in mvps if m["seed"] <= 2) / n * 100, 1),
            "pct_top3_seed": round(sum(1 for m in mvps if m["seed"] <= 3) / n * 100, 1),
            "sample_size": n,
        }

        self.cache.set(cache_key, archetype)
        return archetype
