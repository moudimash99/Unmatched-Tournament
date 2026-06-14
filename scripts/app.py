import os
import hashlib
import json
import math
import random
from pathlib import Path
from flask import Flask, request, session, redirect, send_file, Response, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

ROOT_DIR = Path(__file__).resolve().parent.parent
PW_HASH = os.environ.get("PASSWORD_HASH", "")
HTML_FILE = ROOT_DIR / "generated" / "tournament_new.html"
STATE_FILE = ROOT_DIR / "data" / "state.json"

# ---------------------------------------------------------------------------
# Fighter definitions
# ---------------------------------------------------------------------------

TIER_RANK = {"S": 5, "A+": 4, "A": 3, "B": 2, "C": 1}

TIER_COLORS = {
    "S":  "#f59e0b",
    "A+": "#f97316",
    "A":  "#22c55e",
    "B":  "#3b82f6",
    "C":  "#06b6d4",
}

FIGHTERS_LIST = [
    # S tier
    {"id": "ciri",          "name": "Ciri",                    "tier": "S"},
    {"id": "medusa",        "name": "Medusa",                  "tier": "S"},
    {"id": "elektra",       "name": "Elektra",                 "tier": "S"},
    {"id": "achilles",      "name": "Achilles",                "tier": "S"},
    # A+ tier
    {"id": "sun_wukong",    "name": "Sun Wukong",              "tier": "A+"},
    {"id": "yennenga",      "name": "Yennenga",                "tier": "A+"},
    {"id": "ancient_leshen","name": "Ancient Leshen",          "tier": "A+"},
    {"id": "bigfoot",       "name": "Bigfoot",                 "tier": "A+"},
    # A tier
    {"id": "daredevil",     "name": "Daredevil",               "tier": "A"},
    {"id": "bullseye",      "name": "Bullseye",                "tier": "A"},
    {"id": "little_red",    "name": "Little Red Riding Hood",  "tier": "A"},
    {"id": "sinbad",        "name": "Sinbad",                  "tier": "A"},
    {"id": "geralt",        "name": "Geralt of Rivia",         "tier": "A"},
    {"id": "robin_hood",    "name": "Robin Hood",              "tier": "A"},
    # B tier
    {"id": "t_rex",         "name": "T. Rex",                  "tier": "B"},
    {"id": "alice",         "name": "Alice",                   "tier": "B"},
    {"id": "dracula",       "name": "Dracula",                 "tier": "B"},
    {"id": "she_hulk",      "name": "She-Hulk",                "tier": "B"},
    {"id": "spider_man",    "name": "Spider-Man",              "tier": "B"},
    {"id": "nikola_tesla",  "name": "Nikola Tesla",            "tier": "B"},
    {"id": "golden_bat",    "name": "The Golden Bat",          "tier": "B"},
    {"id": "black_widow",   "name": "Black Widow",             "tier": "B"},
    # C tier
    {"id": "luke_cage",     "name": "Luke Cage",               "tier": "C"},
    {"id": "raptors",       "name": "Raptors",                 "tier": "C"},
    {"id": "moon_knight",   "name": "Moon Knight",             "tier": "C"},
    {"id": "ghost_rider",   "name": "Ghost Rider",             "tier": "C"},
    {"id": "houdini",       "name": "Houdini",                 "tier": "C"},
    {"id": "the_genie",     "name": "The Genie",               "tier": "C"},
    {"id": "ms_marvel",     "name": "Ms. Marvel",              "tier": "C"},
    {"id": "squirrel_girl", "name": "Squirrel Girl",           "tier": "C"},
    {"id": "black_panther", "name": "Black Panther",           "tier": "C"},
    {"id": "doctor_strange","name": "Doctor Strange",          "tier": "C"},
]

FIGHTERS = {f["id"]: f for f in FIGHTERS_LIST}
for fid, f in FIGHTERS.items():
    f["tc"] = TIER_COLORS[f["tier"]]


def _det_noise(a: str, b: str) -> float:
    """Deterministic noise in range (-5, +5) from fighter pair."""
    h = int(hashlib.md5(f"{a}:{b}".encode()).hexdigest(), 16)
    return (h % 201 - 100) / 20.0


def _wp(a: str, b: str) -> float:
    """Win percentage of a vs b, clamped to [5, 95]."""
    ra = TIER_RANK.get(FIGHTERS[a]["tier"], 1)
    rb = TIER_RANK.get(FIGHTERS[b]["tier"], 1)
    noise = _det_noise(a, b)
    raw = 50.0 + (ra - rb) * 8.0 + noise
    return max(5.0, min(95.0, round(raw, 1)))


# Pre-compute full 32×32 win% matrix
WIN_PCT: dict[str, dict[str, float]] = {}
for _a in FIGHTERS:
    WIN_PCT[_a] = {}
    for _b in FIGHTERS:
        if _a != _b:
            WIN_PCT[_a][_b] = _wp(_a, _b)


# ---------------------------------------------------------------------------
# Bracket definition
# ---------------------------------------------------------------------------

# Default R1 pairings (intentionally unbalanced: S vs C, A+ vs C, A vs B)
R1_PAIRINGS = [
    ("r1_1",  "ciri",          "luke_cage",     "Match 1"),
    ("r1_2",  "medusa",        "ghost_rider",   "Match 2"),
    ("r1_3",  "elektra",       "raptors",       "Match 3"),
    ("r1_4",  "achilles",      "moon_knight",   "Match 4"),
    ("r1_5",  "sun_wukong",    "houdini",       "Match 5"),
    ("r1_6",  "yennenga",      "the_genie",     "Match 6"),
    ("r1_7",  "ancient_leshen","ms_marvel",     "Match 7"),
    ("r1_8",  "bigfoot",       "squirrel_girl", "Match 8"),
    ("r1_9",  "daredevil",     "t_rex",         "Match 9"),
    ("r1_10", "bullseye",      "alice",         "Match 10"),
    ("r1_11", "little_red",    "dracula",       "Match 11"),
    ("r1_12", "sinbad",        "she_hulk",      "Match 12"),
    ("r1_13", "geralt",        "spider_man",    "Match 13"),
    ("r1_14", "robin_hood",    "nikola_tesla",  "Match 14"),
    ("r1_15", "golden_bat",    "black_panther", "Match 15"),
    ("r1_16", "black_widow",   "doctor_strange","Match 16"),
]

# R2: winners of R1 pairs
R2_PAIRINGS = [
    ("r2_1", "r1_1",  "r1_2",  "R2-1"),
    ("r2_2", "r1_3",  "r1_4",  "R2-2"),
    ("r2_3", "r1_5",  "r1_6",  "R2-3"),
    ("r2_4", "r1_7",  "r1_8",  "R2-4"),
    ("r2_5", "r1_9",  "r1_10", "R2-5"),
    ("r2_6", "r1_11", "r1_12", "R2-6"),
    ("r2_7", "r1_13", "r1_14", "R2-7"),
    ("r2_8", "r1_15", "r1_16", "R2-8"),
]

QF_PAIRINGS = [
    ("qf_1", "r2_1", "r2_2", "QF-1"),
    ("qf_2", "r2_3", "r2_4", "QF-2"),
    ("qf_3", "r2_5", "r2_6", "QF-3"),
    ("qf_4", "r2_7", "r2_8", "QF-4"),
]

SF_PAIRINGS = [
    ("sf_1", "qf_1", "qf_2", "SF-1"),
    ("sf_2", "qf_3", "qf_4", "SF-2"),
]

FINAL_PAIRINGS = [
    ("final", "sf_1", "sf_2", "Final"),
]


def _fighter_slot(fid: str) -> dict:
    f = FIGHTERS[fid]
    return {"type": "known", "id": fid, "name": f["name"], "tier": f["tier"], "tc": f["tc"]}


def _from_slot(src_mid: str) -> dict:
    return {"type": "from_match", "src": src_mid}


def _meta(top_id: str, bot_id: str) -> dict:
    wp = WIN_PCT[top_id][bot_id]
    wp_b = WIN_PCT[bot_id][top_id]
    denied = abs(wp - 50) > 8
    return {"wp": wp, "wp_b": wp_b, "denied": denied}


def _build_bracket() -> dict:
    bk = {}

    for mid, top_id, bot_id, label in R1_PAIRINGS:
        bk[mid] = {
            "id": mid,
            "label": label,
            "round": 1,
            "top": _fighter_slot(top_id),
            "bot": _fighter_slot(bot_id),
            "preset_winner": None,
            "meta": _meta(top_id, bot_id),
        }

    for mid, src_top, src_bot, label in R2_PAIRINGS:
        bk[mid] = {
            "id": mid,
            "label": label,
            "round": 2,
            "top": _from_slot(src_top),
            "bot": _from_slot(src_bot),
            "preset_winner": None,
            "meta": None,
        }

    for mid, src_top, src_bot, label in QF_PAIRINGS:
        bk[mid] = {
            "id": mid,
            "label": label,
            "round": 3,
            "top": _from_slot(src_top),
            "bot": _from_slot(src_bot),
            "preset_winner": None,
            "meta": None,
        }

    for mid, src_top, src_bot, label in SF_PAIRINGS:
        bk[mid] = {
            "id": mid,
            "label": label,
            "round": 4,
            "top": _from_slot(src_top),
            "bot": _from_slot(src_bot),
            "preset_winner": None,
            "meta": None,
        }

    for mid, src_top, src_bot, label in FINAL_PAIRINGS:
        bk[mid] = {
            "id": mid,
            "label": label,
            "round": 5,
            "top": _from_slot(src_top),
            "bot": _from_slot(src_bot),
            "preset_winner": None,
            "meta": None,
        }

    return bk


BRACKET = _build_bracket()


# ---------------------------------------------------------------------------
# Simulated annealing rebalancer
# ---------------------------------------------------------------------------

def sa_rebalance(fids: list[str], n_iter: int = 12000) -> list[tuple[str, str]]:
    """
    Takes an even-length list of fighter IDs.
    Returns optimal pairings as list of (top_id, bot_id) tuples minimising
    total |wp - 50|.
    Uses simulated annealing: T=10, decay=0.9993.
    """
    n = len(fids)
    assert n % 2 == 0, "Need even number of fighters"
    n_pairs = n // 2

    def total_imbalance(pairs: list[tuple[str, str]]) -> float:
        return sum(abs(WIN_PCT[a][b] - 50.0) for a, b in pairs)

    # Build initial pairing: sequential
    pairs = [(fids[i * 2], fids[i * 2 + 1]) for i in range(n_pairs)]
    best_pairs = list(pairs)
    best_cost = total_imbalance(pairs)
    current_cost = best_cost

    rng = random.Random(42)
    T = 10.0
    decay = 0.9993

    for _ in range(n_iter):
        # Pick two random fighters and swap them
        # Choose two distinct pair indices
        i = rng.randrange(n_pairs)
        j = rng.randrange(n_pairs)
        while j == i:
            j = rng.randrange(n_pairs)

        # Choose a side from each pair to swap (0=top, 1=bot)
        si = rng.randint(0, 1)
        sj = rng.randint(0, 1)

        ai, bi = pairs[i]
        aj, bj = pairs[j]

        # Build new pairs with the swap
        new_pairs = list(pairs)
        p_i = [ai, bi]
        p_j = [aj, bj]
        p_i[si], p_j[sj] = p_j[sj], p_i[si]
        new_pairs[i] = (p_i[0], p_i[1])
        new_pairs[j] = (p_j[0], p_j[1])

        # Skip if a fighter is paired with themselves
        if new_pairs[i][0] == new_pairs[i][1] or new_pairs[j][0] == new_pairs[j][1]:
            continue

        old_cost_ij = (
            abs(WIN_PCT[ai][bi] - 50.0) +
            abs(WIN_PCT[aj][bj] - 50.0)
        )
        new_cost_ij = (
            abs(WIN_PCT[new_pairs[i][0]][new_pairs[i][1]] - 50.0) +
            abs(WIN_PCT[new_pairs[j][0]][new_pairs[j][1]] - 50.0)
        )
        delta = new_cost_ij - old_cost_ij
        new_cost = current_cost + delta

        if delta <= 0 or rng.random() < math.exp(-delta / T):
            pairs = new_pairs
            current_cost = new_cost
            if current_cost < best_cost:
                best_cost = current_cost
                best_pairs = list(pairs)

        T *= decay

    return best_pairs


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _auth_ok() -> bool:
    if not PW_HASH:
        return True
    return bool(session.get("auth"))


def _check_pw(pw: str) -> bool:
    return hashlib.sha256(pw.encode()).hexdigest() == PW_HASH


LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Unmatched Tournament</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:#0f172a;color:#e2e8f0;display:flex;align-items:center;
     justify-content:center;min-height:100vh;
     font-family:'Segoe UI',system-ui,sans-serif}
.card{background:#1e293b;border:1px solid #334155;border-radius:16px;
      padding:2.5rem 2rem;width:320px;text-align:center}
h1{color:#f59e0b;font-size:1.4rem;margin-bottom:.35rem}
p{color:#64748b;font-size:.82rem;margin-bottom:1.5rem}
input[type=password]{width:100%;padding:.65rem 1rem;border-radius:8px;
  border:1.5px solid #334155;background:#0f172a;color:#e2e8f0;
  font-size:.95rem;outline:none;margin-bottom:.9rem;transition:border-color .2s}
input[type=password]:focus{border-color:#f59e0b}
button{width:100%;padding:.65rem;border-radius:8px;border:none;
  background:#f59e0b;color:#000;font-size:.9rem;font-weight:700;
  cursor:pointer;transition:opacity .15s}
button:hover{opacity:.88}
.err{color:#ef4444;font-size:.75rem;margin-top:.5rem}
</style></head>
<body>
<div class="card">
  <h1>&#9876; Unmatched Tournament</h1>
  <p>Enter password to access the tournament</p>
  <form method="POST">
    <input type="password" name="password" placeholder="Password" autofocus>
    <button type="submit">Enter</button>
    {error}
  </form>
</div>
</body></html>"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    if _auth_ok():
        return send_file(str(HTML_FILE))
    if request.method == "POST":
        if _check_pw(request.form.get("password", "")):
            session["auth"] = True
            return redirect("/")
        return LOGIN_PAGE.replace("{error}", '<p class="err">Incorrect password</p>'), 401
    return LOGIN_PAGE.replace("{error}", "")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/api/bracket")
def api_bracket():
    if not _auth_ok():
        return "", 401
    return jsonify(BRACKET)


@app.route("/api/winpct")
def api_winpct():
    if not _auth_ok():
        return "", 401
    a = request.args.get("a", "")
    b = request.args.get("b", "")
    if not a or not b or a not in FIGHTERS or b not in FIGHTERS:
        return jsonify({"wp": None, "wp_b": None})
    return jsonify({"wp": WIN_PCT[a][b], "wp_b": WIN_PCT[b][a]})


@app.route("/api/state", methods=["GET"])
def get_state():
    if not _auth_ok():
        return "", 401
    if STATE_FILE.exists():
        return Response(STATE_FILE.read_text(encoding="utf-8"), content_type="application/json")
    return Response("{}", content_type="application/json")


@app.route("/api/state", methods=["POST"])
def set_state():
    if not _auth_ok():
        return "", 401
    data = request.get_json(force=True, silent=True)
    if data is None:
        return "", 400
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data), encoding="utf-8")
    return "", 204


@app.route("/api/rebalance", methods=["POST"])
def api_rebalance():
    if not _auth_ok():
        return "", 401
    body = request.get_json(force=True, silent=True) or {}
    fids = body.get("fighters", [])
    if not fids or len(fids) % 2 != 0:
        return jsonify({"error": "fighters must be a non-empty even-length list"}), 400
    for fid in fids:
        if fid not in FIGHTERS:
            return jsonify({"error": f"unknown fighter: {fid}"}), 400

    best_pairs = sa_rebalance(fids)

    total_imbalance = sum(abs(WIN_PCT[a][b] - 50.0) for a, b in best_pairs)
    all_balanced = all(abs(WIN_PCT[a][b] - 50.0) <= 5.0 for a, b in best_pairs)

    pairs_out = []
    for top_id, bot_id in best_pairs:
        tf = FIGHTERS[top_id]
        bf = FIGHTERS[bot_id]
        wp = WIN_PCT[top_id][bot_id]
        wp_b = WIN_PCT[bot_id][top_id]
        pairs_out.append({
            "top": {"id": top_id, "name": tf["name"], "tier": tf["tier"], "tc": tf["tc"]},
            "bot": {"id": bot_id, "name": bf["name"], "tier": bf["tier"], "tc": bf["tc"]},
            "wp": wp,
            "wp_b": wp_b,
            "denied": abs(wp - 50.0) > 8,
        })

    return jsonify({
        "pairs": pairs_out,
        "total_imbalance": round(total_imbalance, 2),
        "all_balanced": all_balanced,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8742))
    app.run(host="0.0.0.0", port=port, debug=False)
