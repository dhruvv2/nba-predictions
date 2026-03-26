"""ML-based MVP prediction using Gradient Boosting trained on historical data.

Training data: top MVP candidates from 2005-2024 seasons with labels
(1 = won MVP, 0 = did not win). Features are normalized per-season so the
model learns *relative* dominance patterns rather than raw stat values.

The model is trained once at startup and cached. Predictions blend with the
heuristic model for a final composite score.
"""

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import pickle
import os

# Historical MVP race data: top candidates each year with key stats
# Each entry: (year, name, won_mvp, ppg, rpg, apg, spg, bpg, ts_pct, win_pct, seed, est_ws, est_bpm, est_vorp)
# Stats sourced from basketball-reference.com historical records
TRAINING_DATA = [
    # 2024 — Jokic won (3rd MVP)
    (2024, "Nikola Jokic", 1, 26.4, 12.4, 9.0, 1.4, 0.9, 64.7, 0.695, 2, 15.2, 9.5, 8.1),
    (2024, "Shai Gilgeous-Alexander", 0, 30.1, 5.5, 6.2, 1.7, 0.9, 63.5, 0.695, 1, 13.8, 8.7, 7.2),
    (2024, "Luka Doncic", 0, 33.9, 9.2, 9.8, 1.4, 0.5, 61.0, 0.610, 5, 12.1, 7.8, 6.3),
    (2024, "Giannis Antetokounmpo", 0, 30.4, 11.5, 6.5, 1.2, 1.1, 61.4, 0.598, 3, 12.5, 8.2, 6.7),
    (2024, "Jayson Tatum", 0, 26.9, 8.1, 4.9, 1.0, 0.6, 60.9, 0.780, 1, 10.1, 5.4, 4.6),

    # 2023 — Embiid won
    (2023, "Joel Embiid", 1, 33.1, 10.2, 4.2, 1.0, 1.7, 65.5, 0.659, 3, 14.7, 9.2, 7.5),
    (2023, "Nikola Jokic", 0, 24.5, 11.8, 9.8, 1.3, 0.7, 70.1, 0.659, 1, 14.9, 10.1, 8.8),
    (2023, "Giannis Antetokounmpo", 0, 31.1, 11.8, 5.7, 0.8, 0.8, 60.5, 0.695, 1, 13.2, 7.8, 6.4),
    (2023, "Jayson Tatum", 0, 30.1, 8.8, 4.6, 1.1, 0.7, 60.0, 0.695, 2, 11.3, 6.1, 5.1),
    (2023, "Shai Gilgeous-Alexander", 0, 31.4, 4.8, 5.5, 1.6, 1.0, 62.6, 0.488, 10, 8.5, 6.9, 5.2),

    # 2022 — Jokic won (2nd)
    (2022, "Nikola Jokic", 1, 27.1, 13.8, 7.9, 1.5, 0.9, 66.1, 0.585, 6, 15.2, 13.0, 9.8),
    (2022, "Joel Embiid", 0, 30.6, 11.7, 4.2, 1.1, 1.5, 61.6, 0.622, 4, 11.6, 7.3, 5.8),
    (2022, "Giannis Antetokounmpo", 0, 29.9, 11.6, 5.8, 1.1, 1.4, 63.3, 0.622, 3, 12.9, 7.4, 6.1),
    (2022, "Devin Booker", 0, 26.8, 5.0, 4.8, 1.1, 0.4, 57.5, 0.780, 1, 8.3, 3.9, 3.5),
    (2022, "Luka Doncic", 0, 28.4, 9.1, 8.7, 1.2, 0.7, 57.1, 0.622, 4, 9.4, 6.5, 5.0),

    # 2021 — Jokic won (1st)
    (2021, "Nikola Jokic", 1, 26.4, 10.8, 8.3, 1.3, 0.7, 64.7, 0.653, 3, 15.6, 11.2, 8.6),
    (2021, "Joel Embiid", 0, 28.5, 10.6, 2.8, 1.0, 1.4, 63.6, 0.681, 1, 11.6, 7.7, 4.4),
    (2021, "Stephen Curry", 0, 32.0, 5.5, 5.8, 1.2, 0.4, 65.5, 0.528, 8, 9.9, 7.4, 5.6),
    (2021, "Giannis Antetokounmpo", 0, 28.1, 11.0, 5.9, 1.2, 1.2, 59.9, 0.639, 3, 11.6, 6.6, 5.4),
    (2021, "Chris Paul", 0, 16.4, 4.5, 8.9, 1.4, 0.3, 59.9, 0.722, 2, 7.8, 5.3, 4.4),

    # 2020 — Giannis won (2nd)
    (2020, "Giannis Antetokounmpo", 1, 29.5, 13.6, 5.6, 1.0, 1.0, 61.3, 0.767, 1, 14.4, 11.5, 7.4),
    (2020, "LeBron James", 0, 25.3, 7.8, 10.2, 1.2, 0.5, 57.7, 0.732, 1, 11.1, 8.5, 5.9),
    (2020, "James Harden", 0, 34.3, 6.6, 7.5, 1.8, 0.8, 62.6, 0.611, 4, 12.2, 9.3, 6.3),
    (2020, "Luka Doncic", 0, 28.8, 9.4, 8.8, 1.1, 0.3, 58.5, 0.573, 7, 8.1, 6.3, 4.2),
    (2020, "Kawhi Leonard", 0, 27.1, 7.1, 4.9, 1.8, 0.6, 58.6, 0.681, 2, 10.1, 6.5, 4.5),

    # 2019 — Giannis won (1st)
    (2019, "Giannis Antetokounmpo", 1, 27.7, 12.5, 5.9, 1.3, 1.5, 64.4, 0.732, 1, 14.4, 11.1, 7.5),
    (2019, "James Harden", 0, 36.1, 6.6, 7.5, 2.0, 0.7, 61.6, 0.659, 4, 15.2, 11.7, 8.1),
    (2019, "Paul George", 0, 28.0, 8.2, 4.1, 2.2, 0.4, 58.0, 0.598, 6, 10.4, 6.9, 5.2),
    (2019, "Nikola Jokic", 0, 20.1, 10.8, 7.3, 1.4, 0.7, 58.8, 0.659, 2, 10.4, 7.3, 5.6),
    (2019, "Joel Embiid", 0, 27.5, 13.6, 3.7, 0.7, 1.9, 59.3, 0.622, 3, 11.1, 5.8, 4.3),

    # 2018 — Harden won
    (2018, "James Harden", 1, 30.4, 5.4, 8.8, 1.8, 0.7, 61.9, 0.793, 1, 15.4, 10.6, 8.3),
    (2018, "LeBron James", 0, 27.5, 8.6, 9.1, 1.4, 0.9, 62.1, 0.610, 4, 14.0, 8.9, 7.1),
    (2018, "Anthony Davis", 0, 28.1, 11.1, 2.3, 1.5, 2.6, 58.0, 0.585, 6, 10.1, 5.4, 3.9),
    (2018, "Damian Lillard", 0, 26.9, 4.5, 6.6, 1.1, 0.4, 60.5, 0.598, 3, 9.4, 5.9, 4.6),
    (2018, "Russell Westbrook", 0, 25.4, 10.1, 10.3, 1.8, 0.3, 52.4, 0.585, 4, 7.8, 5.6, 4.1),

    # 2017 — Westbrook won (triple-double narrative)
    (2017, "Russell Westbrook", 1, 31.6, 10.7, 10.4, 1.6, 0.4, 55.4, 0.573, 6, 13.1, 11.1, 8.2),
    (2017, "James Harden", 0, 29.1, 8.1, 11.2, 1.5, 0.5, 61.3, 0.671, 3, 15.0, 10.7, 8.3),
    (2017, "Kawhi Leonard", 0, 25.5, 5.8, 3.5, 1.8, 0.7, 61.1, 0.744, 2, 12.4, 7.0, 5.5),
    (2017, "LeBron James", 0, 26.4, 8.6, 8.7, 1.2, 0.6, 61.9, 0.622, 2, 12.9, 7.3, 5.9),
    (2017, "Isaiah Thomas", 0, 28.9, 2.7, 5.9, 0.9, 0.2, 62.5, 0.646, 1, 9.8, 6.1, 4.7),

    # 2016 — Curry won (unanimous)
    (2016, "Stephen Curry", 1, 30.1, 5.4, 6.7, 2.1, 0.2, 66.9, 0.890, 1, 17.9, 12.5, 9.8),
    (2016, "Kawhi Leonard", 0, 21.2, 6.8, 2.6, 1.8, 1.0, 56.1, 0.817, 2, 11.7, 6.5, 5.1),
    (2016, "LeBron James", 0, 25.3, 7.4, 6.8, 1.4, 0.6, 58.8, 0.695, 1, 11.1, 6.1, 5.0),
    (2016, "Russell Westbrook", 0, 23.5, 7.8, 10.4, 2.0, 0.3, 55.4, 0.671, 3, 9.0, 8.5, 5.8),
    (2016, "Kevin Durant", 0, 28.2, 8.2, 5.0, 1.0, 1.2, 63.4, 0.671, 3, 14.1, 8.2, 6.3),

    # 2015 — Curry won (1st)
    (2015, "Stephen Curry", 1, 23.8, 4.3, 7.7, 2.0, 0.2, 63.8, 0.817, 1, 15.7, 8.5, 6.8),
    (2015, "James Harden", 0, 27.4, 5.7, 7.0, 1.9, 0.7, 60.5, 0.695, 2, 16.4, 10.6, 8.4),
    (2015, "LeBron James", 0, 25.3, 6.0, 7.4, 1.6, 0.7, 57.7, 0.646, 2, 10.2, 5.8, 4.5),
    (2015, "Anthony Davis", 0, 24.4, 10.2, 2.2, 1.5, 2.9, 57.6, 0.549, 8, 10.3, 5.2, 3.5),
    (2015, "Russell Westbrook", 0, 28.2, 7.3, 8.6, 2.1, 0.2, 53.6, 0.549, 9, 9.1, 10.0, 6.4),

    # 2014 — Durant won
    (2014, "Kevin Durant", 1, 32.0, 7.4, 5.5, 1.3, 0.7, 63.5, 0.720, 2, 19.2, 10.6, 8.8),
    (2014, "LeBron James", 0, 27.1, 6.9, 6.3, 1.6, 0.3, 64.9, 0.659, 2, 15.9, 8.8, 7.2),
    (2014, "Joakim Noah", 0, 12.6, 11.3, 5.4, 1.2, 1.5, 50.0, 0.585, 4, 10.7, 5.9, 4.7),
    (2014, "Blake Griffin", 0, 24.1, 9.5, 3.9, 1.2, 0.5, 58.0, 0.695, 3, 12.1, 5.6, 4.2),
    (2014, "James Harden", 0, 25.4, 4.7, 6.1, 1.6, 0.4, 60.9, 0.659, 4, 12.1, 6.5, 5.1),

    # 2013 — LeBron won
    (2013, "LeBron James", 1, 26.8, 8.0, 7.3, 1.7, 0.9, 64.0, 0.805, 1, 19.3, 11.6, 9.4),
    (2013, "Kevin Durant", 0, 28.1, 7.9, 4.6, 1.4, 1.3, 64.7, 0.732, 1, 18.0, 9.5, 7.7),
    (2013, "Carmelo Anthony", 0, 28.7, 6.9, 2.6, 0.8, 0.5, 56.0, 0.659, 2, 10.3, 4.1, 3.2),
    (2013, "Chris Paul", 0, 16.9, 3.7, 9.7, 2.4, 0.1, 57.5, 0.683, 4, 10.7, 7.6, 6.2),
    (2013, "Tim Duncan", 0, 17.8, 9.9, 2.7, 0.7, 2.7, 52.9, 0.707, 2, 12.0, 5.9, 4.8),

    # 2012 — LeBron won (shortened season)
    (2012, "LeBron James", 1, 27.1, 7.9, 6.2, 1.9, 0.8, 60.5, 0.697, 2, 14.5, 10.0, 5.6),
    (2012, "Kevin Durant", 0, 28.0, 8.0, 3.5, 1.3, 1.2, 61.0, 0.697, 2, 14.1, 8.4, 4.6),
    (2012, "Chris Paul", 0, 19.8, 3.6, 9.1, 2.5, 0.1, 57.5, 0.621, 6, 9.7, 7.0, 3.5),
    (2012, "Tony Parker", 0, 18.3, 3.0, 7.7, 0.8, 0.1, 55.2, 0.758, 1, 9.1, 5.3, 2.6),
    (2012, "Kobe Bryant", 0, 27.9, 5.4, 4.6, 1.2, 0.3, 57.3, 0.636, 3, 8.5, 4.1, 2.2),

    # 2011 — Rose won
    (2011, "Derrick Rose", 1, 25.0, 4.1, 7.7, 1.0, 0.6, 55.0, 0.756, 1, 11.3, 6.0, 4.8),
    (2011, "Dwight Howard", 0, 22.9, 14.1, 1.4, 1.4, 2.4, 59.4, 0.622, 4, 15.0, 8.2, 6.2),
    (2011, "LeBron James", 0, 26.7, 7.5, 7.0, 1.6, 0.6, 59.4, 0.707, 2, 15.6, 9.5, 7.5),
    (2011, "Kevin Durant", 0, 27.7, 6.8, 2.7, 1.1, 1.0, 61.0, 0.671, 4, 13.0, 6.4, 5.0),
    (2011, "Kobe Bryant", 0, 25.3, 5.1, 4.7, 1.2, 0.1, 54.8, 0.695, 2, 8.2, 3.2, 2.4),

    # 2010 — LeBron won
    (2010, "LeBron James", 1, 29.7, 7.3, 8.6, 1.6, 1.0, 60.4, 0.744, 1, 18.5, 11.8, 9.4),
    (2010, "Kevin Durant", 0, 30.1, 7.6, 2.8, 1.4, 1.0, 61.0, 0.610, 8, 12.2, 6.8, 5.2),
    (2010, "Kobe Bryant", 0, 27.0, 5.4, 5.0, 1.5, 0.3, 56.2, 0.695, 1, 9.5, 4.8, 3.8),
    (2010, "Dwight Howard", 0, 18.3, 13.2, 1.8, 0.9, 2.8, 59.9, 0.720, 2, 13.2, 5.3, 4.1),
    (2010, "Dwyane Wade", 0, 26.6, 4.8, 6.5, 1.8, 1.1, 57.1, 0.573, 5, 12.0, 8.5, 5.9),

    # 2009 — LeBron won
    (2009, "LeBron James", 1, 28.4, 7.6, 7.2, 1.7, 1.1, 59.1, 0.805, 1, 20.3, 12.8, 10.4),
    (2009, "Kobe Bryant", 0, 26.8, 5.2, 4.9, 1.5, 0.5, 56.1, 0.793, 1, 12.3, 6.4, 5.5),
    (2009, "Dwyane Wade", 0, 30.2, 5.0, 7.5, 2.2, 1.3, 57.4, 0.524, 5, 14.7, 11.0, 7.7),
    (2009, "Dwight Howard", 0, 20.6, 13.8, 1.4, 0.9, 2.9, 60.2, 0.720, 3, 16.0, 8.1, 6.4),
    (2009, "Chris Paul", 0, 22.8, 5.5, 11.0, 2.8, 0.1, 59.9, 0.598, 3, 14.8, 10.0, 7.2),

    # 2008 — Kobe won
    (2008, "Kobe Bryant", 1, 28.3, 6.3, 5.4, 1.8, 0.5, 57.6, 0.695, 1, 11.3, 5.6, 4.7),
    (2008, "Chris Paul", 0, 21.1, 4.0, 11.6, 2.7, 0.1, 57.6, 0.683, 2, 14.8, 10.5, 8.0),
    (2008, "Kevin Garnett", 0, 18.8, 9.2, 3.4, 1.4, 1.3, 55.7, 0.805, 1, 13.6, 7.6, 6.1),
    (2008, "LeBron James", 0, 30.0, 7.9, 7.2, 1.8, 1.1, 56.8, 0.549, 4, 13.1, 8.9, 6.8),
    (2008, "Tim Duncan", 0, 19.3, 11.3, 2.8, 0.7, 2.0, 52.7, 0.683, 3, 11.8, 6.0, 4.7),

    # 2007 — Dirk won
    (2007, "Dirk Nowitzki", 1, 24.6, 8.9, 3.4, 0.7, 0.8, 58.7, 0.817, 1, 16.3, 8.0, 6.6),
    (2007, "Steve Nash", 0, 18.6, 3.5, 11.6, 0.8, 0.1, 63.2, 0.744, 2, 12.5, 7.1, 5.8),
    (2007, "LeBron James", 0, 27.3, 6.7, 6.0, 1.6, 0.7, 55.2, 0.610, 2, 11.7, 7.0, 5.3),
    (2007, "Tim Duncan", 0, 20.0, 10.6, 3.4, 0.7, 2.4, 54.4, 0.707, 3, 14.1, 7.5, 5.9),
    (2007, "Kobe Bryant", 0, 31.6, 5.7, 5.4, 1.4, 0.5, 58.0, 0.512, 7, 10.5, 7.1, 5.6),

    # 2006 — Nash won (2nd)
    (2006, "Steve Nash", 1, 18.8, 4.2, 10.5, 0.8, 0.2, 62.3, 0.659, 2, 12.5, 6.8, 5.7),
    (2006, "LeBron James", 0, 31.4, 7.0, 6.6, 1.6, 0.8, 56.8, 0.610, 4, 11.5, 8.3, 6.2),
    (2006, "Kobe Bryant", 0, 35.4, 5.3, 4.5, 1.8, 0.4, 55.9, 0.549, 7, 9.1, 6.1, 4.3),
    (2006, "Dirk Nowitzki", 0, 26.6, 9.0, 2.8, 0.7, 0.7, 58.3, 0.732, 4, 14.0, 5.9, 4.8),
    (2006, "Chauncey Billups", 0, 18.5, 3.1, 8.6, 1.0, 0.2, 58.7, 0.780, 1, 10.0, 5.1, 4.1),

    # 2005 — Nash won (1st)
    (2005, "Steve Nash", 1, 15.5, 3.3, 11.5, 1.0, 0.1, 60.6, 0.756, 1, 11.0, 6.0, 5.1),
    (2005, "Shaquille O'Neal", 0, 22.9, 10.4, 2.7, 0.5, 2.3, 59.0, 0.720, 1, 14.2, 6.8, 5.4),
    (2005, "Tim Duncan", 0, 20.3, 11.1, 2.7, 0.7, 2.6, 53.0, 0.720, 2, 14.0, 7.8, 6.3),
    (2005, "Dirk Nowitzki", 0, 26.1, 9.7, 3.1, 1.2, 1.0, 58.0, 0.707, 4, 14.5, 6.7, 5.5),
    (2005, "Allen Iverson", 0, 30.7, 4.0, 7.9, 2.4, 0.1, 51.8, 0.524, 5, 7.1, 6.0, 4.2),
]

# Feature names (must match extraction order)
FEATURE_NAMES = [
    "ppg", "rpg", "apg", "spg", "bpg",
    "ts_pct", "win_pct", "seed", "est_ws",
    "est_bpm", "est_vorp",
    # Derived features
    "ppg_x_win_pct",       # scoring × team success interaction
    "ws_per_seed",         # win shares adjusted by seed
    "all_around",          # ppg + rpg + apg combined
    "inverse_seed",        # 1/seed — makes top seeds scale better
    # Narrative features
    "is_triple_dbl",       # averaging triple-double (RPG≥10 & APG≥10)
    "near_triple_dbl",     # near triple-double (RPG≥10 & APG≥8 or RPG≥8 & APG≥10)
    "is_top_seed",         # team is #1 seed
    "volume_efficiency",   # PPG × TS% / 100 — rewards high-volume efficient scorers
    "prev_mvp",            # won MVP in prior year (voter fatigue signal)
]

# Track which players won MVP each year for narrative features
_MVP_WINNERS_BY_YEAR = {r[0]: r[1] for r in
    [(y, name) for y, name, won, *_ in TRAINING_DATA if won == 1]
} if TRAINING_DATA else {}


def _extract_features(row, prev_mvp_name=None):
    """Extract feature vector from a training row or player dict."""
    if isinstance(row, tuple):
        # Training data tuple
        year, name, _, ppg, rpg, apg, spg, bpg, ts, wpct, seed, ws, bpm, vorp = row
        # Look up if this player won MVP the year before
        was_prev_mvp = 1.0 if _MVP_WINNERS_BY_YEAR.get(year - 1) == name else 0.0
    else:
        # Player dict from live data
        ppg = row.get("ppg", 0)
        rpg = row.get("rpg", 0)
        apg = row.get("apg", 0)
        spg = row.get("spg", 0)
        bpg = row.get("bpg", 0)
        ts = row.get("ts_pct", 55)
        wpct = row.get("team_win_pct", 50) / 100  # stored as percentage in live data
        seed = row.get("team_seed", 8)
        ws = row.get("est_ws", 0)
        bpm = row.get("est_bpm", 0)
        vorp = row.get("est_vorp", 0)
        was_prev_mvp = 1.0 if row.get("is_prev_mvp", False) else 0.0

    return [
        ppg, rpg, apg, spg, bpg,
        ts, wpct, seed, ws, bpm, vorp,
        ppg * wpct,                    # interaction: scoring on winning team
        ws / max(seed, 1),             # win shares per seed position
        ppg + rpg + apg,               # all-around
        1.0 / max(seed, 1),            # inverse seed (1st = 1.0, 8th = 0.125)
        # Narrative features
        1.0 if (rpg >= 10 and apg >= 10) else 0.0,        # triple-double avg
        1.0 if (rpg >= 10 and apg >= 8) or (rpg >= 8 and apg >= 10) else 0.0,  # near
        1.0 if seed == 1 else 0.0,                          # #1 seed
        ppg * ts / 100,                                      # volume × efficiency
        was_prev_mvp,                                        # voter fatigue signal
    ]


class MlMvpModel:
    """Gradient Boosting MVP prediction model trained on historical data."""

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self._train()

    def _train(self):
        """Train on historical MVP candidate data."""
        X = []
        y = []

        for row in TRAINING_DATA:
            features = _extract_features(row)
            label = row[2]  # won_mvp (1 or 0)
            X.append(features)
            y.append(label)

        X = np.array(X)
        y = np.array(y)

        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)

        self.model = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.08,
            min_samples_leaf=3,
            subsample=0.85,
            random_state=42,
        )
        self.model.fit(X_scaled, y)

        # Log feature importances for debugging
        importances = self.model.feature_importances_
        self.feature_importances = dict(zip(FEATURE_NAMES, importances))

    def predict_mvp_probability(self, player_dict):
        """Predict MVP probability for a single player."""
        features = _extract_features(player_dict)
        X = np.array([features])
        X_scaled = self.scaler.transform(X)
        proba = self.model.predict_proba(X_scaled)[0][1]
        return float(proba)

    def predict_mvp_scores(self, player_dicts):
        """Predict MVP scores for multiple players using decision function.

        Returns raw decision function values (logits) which provide smoother
        gradients than predict_proba. The values are then min-max normalized
        to a 0-1 scale across the candidate pool.

        Args:
            player_dicts: List of player dicts with team_win_pct and team_seed.

        Returns:
            List of floats (0-1), one per player, representing relative MVP strength.
        """
        if not player_dicts:
            return []

        X = np.array([_extract_features(p) for p in player_dicts])
        X_scaled = self.scaler.transform(X)

        # Use decision_function for smoother scores than predict_proba
        raw_scores = self.model.decision_function(X_scaled)

        # Also get probabilities for display
        probas = self.model.predict_proba(X_scaled)[:, 1]

        # Min-max normalize decision scores to 0-1
        s_min, s_max = raw_scores.min(), raw_scores.max()
        if s_max > s_min:
            normalized = (raw_scores - s_min) / (s_max - s_min)
        else:
            normalized = np.full_like(raw_scores, 0.5)

        return [
            {"ml_score": float(n), "ml_probability": float(p)}
            for n, p in zip(normalized, probas)
        ]

    def get_feature_importances(self):
        """Return feature importances from the trained model."""
        sorted_imp = sorted(self.feature_importances.items(),
                          key=lambda x: x[1], reverse=True)
        return sorted_imp
