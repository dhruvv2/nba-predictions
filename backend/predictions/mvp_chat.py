"""MVP Chat engine — answers questions about MVP rankings using live data.

No external LLM required. Uses pattern matching + actual MVP ranking data
to construct intelligent, data-driven responses about why players are
ranked where they are, comparisons between candidates, and methodology.
"""

import re
from difflib import get_close_matches


# Methodology explanations
METHODOLOGY = {
    "score": "The MVP Score is a blend of 60% heuristic model (hand-tuned weights calibrated to 20 years of MVP voting) and 40% ML model (Gradient Boosting trained on 100 historical MVP candidates from 2005-2024). The heuristic model uses 12 weighted components, while the ML model uses 20 features including narrative factors.",
    "narrative": "The Narrative Score captures storyline elements that pure stats miss: voter fatigue (penalty for defending MVPs), fresh face bonus (never won before), triple-double milestones, scoring title, #1 seed narrative, and historic efficiency. These factors historically swing close MVP races — e.g., Westbrook's triple-double in 2017, Rose's youngest MVP in 2011.",
    "ml": "The ML model is a Gradient Boosting classifier trained on the top 5 MVP candidates from each season (2005-2024). It uses 20 features including stats, team context, interaction terms, and narrative signals. In cross-validation, it picks the winner 45% of the time and has the winner in the top 3 95% of the time.",
    "weights": "Heuristic weights: Team Success 15%, Win Shares 13%, Scoring 13%, Narrative 10%, All-Around 10%, Advanced Stats 10%, Clutch 6%, BPM 5%, Archetype 5%, Defense 5%, Availability 5%, FG% 3%.",
    "eligibility": "Since 2023-24, players need 65 games played at 20+ minutes to be eligible for end-of-season awards including MVP. Players are marked: ✅ Eligible (65+ GP), ⏳ Projected (on pace), ❌ Ineligible.",
    "win_shares": "Win Shares estimate how many wins a player contributes. The WS leader won MVP in 14 of 20 seasons (2005-2024). We estimate WS from PIE (Player Impact Estimate), games played, and minutes.",
    "team_success": "Team success is crucial — a top-3 seed won MVP 19 of 20 times from 2005-2024. The only exception was Jokic in 2022 (6th seed) who had historically dominant advanced stats.",
    "clutch": "Clutch stats measure performance in the last 5 minutes of games within 5 points. This captures 'big moment' players who elevate when it matters most.",
    "advanced": "Advanced stats include True Shooting % (scoring efficiency), PIE (overall impact), and Net Rating (point differential per 100 possessions with the player on court).",
    "per": "PER (Player Efficiency Rating) is a per-minute rating that accounts for all positive and negative box score contributions. League average is 15. MVP winners typically have PER of 25+.",
    "bpm": "BPM (Box Plus/Minus) estimates a player's contribution per 100 possessions above league average. Positive = above average. MVP winners typically have BPM of 8+.",
    "vorp": "VORP (Value Over Replacement Player) = BPM scaled by playing time. It measures total value added compared to a replacement-level player over the season.",
}

STAT_LABELS = {
    "ppg": "points per game", "rpg": "rebounds per game", "apg": "assists per game",
    "spg": "steals per game", "bpg": "blocks per game", "ts_pct": "True Shooting %",
    "pie": "Player Impact Estimate", "net_rating": "Net Rating", "est_ws": "Win Shares",
    "est_per": "estimated PER", "est_bpm": "estimated BPM", "est_vorp": "estimated VORP",
    "clutch_ppg": "clutch PPG", "ast_tov": "AST/TOV ratio",
    "team_seed": "team seed", "team_win_pct": "team win %",
    "games": "games played", "mpg": "minutes per game",
}


# Common nicknames and abbreviations
NICKNAMES = {
    "sga": "gilgeous-alexander", "jokic": "jokić", "jokić": "jokić",
    "luka": "dončić", "doncic": "dončić", "giannis": "antetokounmpo",
    "the greek freak": "antetokounmpo", "greek freak": "antetokounmpo",
    "wemby": "wembanyama", "wembanyama": "wembanyama",
    "embiid": "embiid", "lebron": "james", "steph": "curry",
    "curry": "curry", "kd": "durant", "durant": "durant",
    "ant": "edwards", "tatum": "tatum", "brown": "brown",
    "harden": "harden", "dame": "lillard", "lillard": "lillard",
    "maxey": "maxey", "cade": "cunningham", "murray": "murray",
}


def _resolve_nickname(word):
    """Resolve a nickname/abbreviation to a last name fragment."""
    return NICKNAMES.get(word.lower(), word.lower())


def _find_player(query, rankings):
    """Find a player mentioned in the query."""
    query_lower = query.lower()

    # Check nicknames first
    for nick, target in NICKNAMES.items():
        if nick in query_lower:
            for p in rankings:
                if target in p["name"].lower():
                    return p

    # Direct name match
    for p in rankings:
        name_lower = p["name"].lower()
        if name_lower in query_lower:
            return p
        last_name = name_lower.split()[-1]
        if last_name in query_lower and len(last_name) > 3:
            return p
        first_name = name_lower.split()[0]
        if first_name in query_lower and len(first_name) > 3:
            return p

    # Fuzzy match
    names = [p["name"] for p in rankings]
    words = query.split()
    for word in words:
        if len(word) < 4:
            continue
        matches = get_close_matches(word, [n.split()[-1] for n in names], n=1, cutoff=0.7)
        if matches:
            for p in rankings:
                if p["name"].split()[-1].lower() == matches[0].lower():
                    return p
    return None


def _find_two_players(query, rankings):
    """Find two players for comparison queries."""
    query_lower = query.lower()
    found = []

    # Split on comparison words to get two parts
    split_patterns = [" vs ", " versus ", " compared to ", " or ", " above ", " over ", " instead of ", " better than ", " higher than "]
    parts = [query_lower]
    for pat in split_patterns:
        if pat in query_lower:
            parts = query_lower.split(pat, 1)
            break

    if len(parts) == 2:
        p1 = _find_player(parts[0], rankings)
        p2 = _find_player(parts[1], rankings)
        if p1 and p2 and p1["name"] != p2["name"]:
            return p1, p2

    # Fallback: find all mentioned players
    for p in rankings:
        name_lower = p["name"].lower()
        last_name = name_lower.split()[-1]
        # Check nicknames
        for nick, target in NICKNAMES.items():
            if nick in query_lower and target in name_lower and p not in found:
                found.append(p)
        if name_lower in query_lower or (last_name in query_lower and len(last_name) > 3):
            if p not in found:
                found.append(p)
        if name_lower in query_lower or (last_name in query_lower and len(last_name) > 3):
            found.append(p)
    if len(found) >= 2:
        return found[0], found[1]
    return None, None


def _player_summary(p):
    """Generate a brief stat summary of a player."""
    lines = [f"**{p['name']}** ({p['team']}) — Rank #{p['rank']}, MVP Score: {p['mvp_score']}"]
    lines.append(f"Stats: {p['ppg']} PPG, {p['rpg']} RPG, {p['apg']} APG, {p.get('spg',0)} STL, {p.get('bpg',0)} BLK")
    lines.append(f"Advanced: {p.get('ts_pct',0)}% TS, {p.get('pie',0)} PIE, {p.get('net_rating',0):+.1f} NET, {p.get('est_ws',0)} WS")
    lines.append(f"Team: Seed #{p['team_seed']}, {p['team_win_pct']}% win rate")
    lines.append(f"Narrative: {p['factors'].get('narrative', 'N/A')}/100 | ML Probability: {p.get('ml_probability', 0)}%")
    return "\n".join(lines)


def _comparison(p1, p2):
    """Generate a detailed comparison between two players."""
    lines = [f"**{p1['name']} (#{p1['rank']})** vs **{p2['name']} (#{p2['rank']})**\n"]

    # Score difference
    diff = abs(p1["mvp_score"] - p2["mvp_score"])
    leader = p1 if p1["mvp_score"] > p2["mvp_score"] else p2
    lines.append(f"📊 Score gap: {diff:.1f} points in favor of {leader['name']}\n")

    # Stat comparison
    stats = [
        ("PPG", "ppg"), ("RPG", "rpg"), ("APG", "apg"),
        ("TS%", "ts_pct"), ("WS", "est_ws"), ("PIE", "pie"),
        ("NET", "net_rating"), ("Seed", "team_seed"),
    ]

    advantages_1 = []
    advantages_2 = []
    for label, key in stats:
        v1 = p1.get(key, 0)
        v2 = p2.get(key, 0)
        if key == "team_seed":
            # Lower seed is better
            if v1 < v2:
                advantages_1.append(f"{label} (#{v1} vs #{v2})")
            elif v2 < v1:
                advantages_2.append(f"{label} (#{v2} vs #{v1})")
        else:
            if v1 > v2:
                advantages_1.append(f"{label} ({v1} vs {v2})")
            elif v2 > v1:
                advantages_2.append(f"{label} ({v2} vs {v1})")

    if advantages_1:
        lines.append(f"✅ **{p1['name']}** leads in: {', '.join(advantages_1)}")
    if advantages_2:
        lines.append(f"✅ **{p2['name']}** leads in: {', '.join(advantages_2)}")

    # Factor comparison
    f1 = p1.get("factors", {})
    f2 = p2.get("factors", {})
    lines.append(f"\n📖 Narrative: {p1['name']} {f1.get('narrative','?')} vs {p2['name']} {f2.get('narrative','?')}")
    lines.append(f"🤖 ML Prob: {p1['name']} {p1.get('ml_probability',0)}% vs {p2['name']} {p2.get('ml_probability',0)}%")

    # Key differentiator
    if leader.get("team_seed", 15) <= 2 and (p1 if leader != p1 else p2).get("team_seed", 15) > 3:
        lines.append(f"\n💡 Key factor: **Team seed** — {leader['name']}'s #{leader['team_seed']} seed is a major advantage. Top-3 seeds won MVP 19/20 times.")
    elif leader.get("est_ws", 0) > (p1 if leader != p1 else p2).get("est_ws", 0) + 2:
        lines.append(f"\n💡 Key factor: **Win Shares** — {leader['name']} has a significant WS advantage, the strongest single MVP predictor.")

    return "\n".join(lines)


def _why_ranked(p, rankings):
    """Explain why a player is ranked where they are."""
    lines = [_player_summary(p), ""]

    factors = p.get("factors", {})

    # Strengths
    strengths = []
    if factors.get("team_success", 0) >= 80:
        strengths.append(f"Elite team success (seed #{p['team_seed']}, {p['team_win_pct']}% win rate)")
    if factors.get("scoring", 0) >= 80:
        strengths.append(f"Top-tier scoring ({p['ppg']} PPG)")
    if factors.get("win_shares", 0) >= 80:
        strengths.append(f"Dominant Win Shares ({p.get('est_ws', 0)})")
    if factors.get("narrative", 0) >= 80:
        strengths.append("Strong narrative factor (fresh face / milestone season)")
    if factors.get("all_around", 0) >= 80:
        total = p['ppg'] + p['rpg'] + p['apg']
        strengths.append(f"Elite all-around game ({total:.1f} combined PPG+RPG+APG)")
    if factors.get("advanced", 0) >= 70:
        strengths.append(f"Strong advanced stats ({p.get('ts_pct',0)}% TS, {p.get('pie',0)} PIE)")
    if factors.get("clutch", 0) >= 70:
        strengths.append(f"Clutch performer ({p.get('clutch_ppg', 0)} clutch PPG)")
    if p.get("ml_probability", 0) >= 20:
        strengths.append(f"ML model gives {p['ml_probability']}% win probability")

    # Weaknesses
    weaknesses = []
    if p.get("team_seed", 15) > 5:
        weaknesses.append(f"Low team seed (#{p['team_seed']}) — top-3 seed won 19/20 MVPs")
    if factors.get("narrative", 0) < 50:
        weaknesses.append("Weak narrative (possible voter fatigue or low-seed team)")
    if p.get("ts_pct", 0) < 57:
        weaknesses.append(f"Below-average efficiency ({p.get('ts_pct',0)}% TS)")
    if p.get("games", 0) < 60:
        weaknesses.append(f"Availability concern ({p['games']} GP, needs 65)")
    if factors.get("defense", 0) < 30:
        weaknesses.append("Limited defensive impact")

    if strengths:
        lines.append("**💪 Strengths:**")
        for s in strengths:
            lines.append(f"  • {s}")

    if weaknesses:
        lines.append("\n**⚠️ Holding them back:**")
        for w in weaknesses:
            lines.append(f"  • {w}")

    # Context vs neighbors
    rank = p["rank"]
    above = next((r for r in rankings if r["rank"] == rank - 1), None)
    below = next((r for r in rankings if r["rank"] == rank + 1), None)
    if above:
        gap = above["mvp_score"] - p["mvp_score"]
        lines.append(f"\n📏 Gap to #{rank-1} {above['name']}: {gap:.1f} points")
    if below:
        gap = p["mvp_score"] - below["mvp_score"]
        lines.append(f"📏 Lead over #{rank+1} {below['name']}: {gap:.1f} points")

    return "\n".join(lines)


def _is_comparison(query):
    """Check if query is comparing two players."""
    patterns = [r"\bvs\.?\b", r"\bversus\b", r"\bcompare\b", r"\babove\b",
                r"\bhigher than\b", r"\bbetter than\b", r"\bover\b", r"\binstead of\b"]
    return any(re.search(p, query.lower()) for p in patterns)


def _is_methodology(query):
    """Check if query is about methodology."""
    keywords = ["calculated", "methodology", "formula", "model", "machine learning",
                "weight", "how does the score", "how is .* score"]
    q = query.lower()
    # Must match methodology keywords AND not contain a player reference
    has_keyword = any(k in q for k in keywords) or any(re.search(k, q) for k in keywords if '.' in k)
    # Check for specific methodology topics
    for topic in METHODOLOGY:
        if topic in q:
            return True
    return has_keyword


def _is_not_on_list(query):
    """Check if asking why someone is NOT on the list."""
    patterns = [r"why (?:isn't|isnt|is not|isn)", r"where is", r"not on",
                r"not (?:ranked|listed|included)", r"missing"]
    return any(re.search(p, query.lower()) for p in patterns)


def _is_who_will_win(query):
    """Check if asking who will win MVP."""
    patterns = [r"who (?:will|should|is going to|gonna) win",
                r"who(?:'s| is) (?:the )?(?:mvp|favorite)",
                r"predict(?:ion)?", r"winner"]
    return any(re.search(p, query.lower()) for p in patterns)


def answer_mvp_question(query, rankings):
    """Main entry point — answer an MVP-related question using ranking data.

    Args:
        query: User's question as a string.
        rankings: List of MVP candidate dicts from the predictor.

    Returns:
        String answer.
    """
    if not rankings:
        return "No MVP ranking data is currently available. Please try again later."

    query = query.strip()
    if not query:
        return "Please ask a question about the MVP race!"

    # Who will win?
    if _is_who_will_win(query):
        top = rankings[0]
        second = rankings[1] if len(rankings) > 1 else None
        answer = f"Based on our model, **{top['name']}** is the current MVP frontrunner with a score of {top['mvp_score']} and {top.get('ml_probability', 0)}% ML probability.\n\n"
        answer += _player_summary(top)
        if second:
            gap = top["mvp_score"] - second["mvp_score"]
            answer += f"\n\nClosest challenger: {second['name']} ({second['mvp_score']}) — {gap:.1f} points behind."
        return answer

    # Methodology questions
    if _is_methodology(query):
        q = query.lower()
        for key, explanation in METHODOLOGY.items():
            if key in q or (key == "score" and ("calculated" in q or "how" in q)):
                return explanation
        # General methodology
        return METHODOLOGY["score"] + "\n\n" + METHODOLOGY["weights"]

    # Comparison
    if _is_comparison(query):
        p1, p2 = _find_two_players(query, rankings)
        if p1 and p2:
            return _comparison(p1, p2)

    # Why is someone NOT on the list
    if _is_not_on_list(query):
        player = _find_player(query, rankings)
        if player:
            return f"{player['name']} IS on the list at #{player['rank']}!\n\n" + _player_summary(player)
        else:
            return ("The player you're asking about may not be in the top 15 candidates. Common reasons:\n"
                    "• Not enough games played (need 65 for eligibility)\n"
                    "• Team record too low (19/20 MVPs were on top-3 seeds)\n"
                    "• Stats not in MVP range compared to other candidates\n"
                    "• Player may be injured or load-managing\n\n"
                    f"Current top 3: {rankings[0]['name']}, {rankings[1]['name']}, {rankings[2]['name']}")

    # Specific player question
    player = _find_player(query, rankings)
    if player:
        return _why_ranked(player, rankings)

    # Top N / ranking overview
    if any(w in query.lower() for w in ["top", "ranking", "list", "all", "race", "standings"]):
        lines = ["**🏆 Current MVP Race — Top 10:**\n"]
        for p in rankings[:10]:
            ml = f" (ML: {p.get('ml_probability',0)}%)" if p.get('ml_probability', 0) > 0 else ""
            lines.append(f"#{p['rank']}. **{p['name']}** ({p['team']}) — {p['mvp_score']}{ml}")
            lines.append(f"   {p['ppg']} PPG / {p['rpg']} RPG / {p['apg']} APG | Seed #{p['team_seed']}")
        return "\n".join(lines)

    # Fallback
    return (f"I can help with questions about the MVP race! Try asking:\n"
            f"• \"Why is {rankings[0]['name']} ranked #1?\"\n"
            f"• \"{rankings[0]['name']} vs {rankings[1]['name']}\"\n"
            f"• \"Why isn't [player] higher?\"\n"
            f"• \"Who will win MVP?\"\n"
            f"• \"How is the score calculated?\"\n"
            f"• \"What is the narrative score?\"")
