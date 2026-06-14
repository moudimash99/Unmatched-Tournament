import json, sys, random, math
from itertools import combinations
sys.stdout.reconfigure(encoding="utf-8")

# ── 1. Easy Integration of Played Matches ──────────────────────────────────
PLAYED_MATCHES_INPUT = [
    { "fighter1": "Bullseye", "fighter2": "Spider-Man", "winner": "Bullseye", "winner_player": "P1" },
    { "fighter1": "Robin Hood", "fighter2": "Achilles", "winner": "Robin Hood", "winner_player": "P2" },
    { "fighter1": "Dr. Sattler", "fighter2": "Winter Soldier", "winner": "Dr. Sattler", "winner_player": "P1" },
    { "fighter1": "Bigfoot", "fighter2": "She-Hulk", "winner": "Bigfoot", "winner_player": "P2" },
    { "fighter1": "Black Panther", "fighter2": "Geralt of Rivia", "winner": "Geralt of Rivia", "winner_player": "P2" },
    { "fighter1": "Sun Wukong", "fighter2": "Black Widow", "winner": "Sun Wukong", "winner_player": "P2" },
    { "fighter1": "The Invisible Man", "fighter2": "Ancient Leshen", "winner": "Ancient Leshen", "winner_player": "P1" },
    { "fighter1": "Alice", "fighter2": "Doctor Strange", "winner": "Doctor Strange", "winner_player": "P2" },
    { "fighter1": "The Genie", "fighter2": "Annie Christmas", "winner": "Annie Christmas", "winner_player": "P1" },
    { "fighter1": "Houdini", "fighter2": "Dr. Jill Trent", "winner": "Dr. Jill Trent", "winner_player": "P2" },
    { "fighter1": "Chupacabra", "fighter2": "Eredin", "winner": "Eredin", "winner_player": "P1" },
    { "fighter1": "Loki", "fighter2": "Raptors", "winner": "Raptors", "winner_player": "P1" }
]

# ── Load Data ──────────────────────────────────────────────────────────────
with open("data/merged_win_pct.json") as f:
    matrix = json.load(f)

with open("data/fighters.json") as f:
    NAME = {f["id"]: f["name"] for f in json.load(f)["fighters"]}
NAME.update({"the_golden_bat":"The Golden Bat","philippa_eilhart":"Philippa Eilhart","eredin":"Eredin Breacc Glas"})
def n(fid): return NAME.get(fid, fid.replace("_"," ").title())

TIER_DATA = [
    ("S",  ["ciri","medusa","sherlock_holmes","elektra","achilles"]),
    ("A+", ["ancient_leshen","sun_wukong","yennenga","bigfoot"]),
    ("A",  ["daredevil","bullseye","little_red","sinbad","geralt","robin_hood","blackbeard"]),
    ("B",  ["t_rex","alice","dracula","she_hulk","spider_man","nikola_tesla",
            "dr_jill_trent","annie_christmas","the_golden_bat","winter_soldier",
            "black_widow","bloody_mary","chupacabra","pandora"]),
    ("C",  ["luke_cage","raptors","invisible_man","jekyll_hyde","moon_knight",
            "ghost_rider","houdini","the_genie","ms_marvel","squirrel_girl",
            "cloak_and_dagger","black_panther","doctor_strange","eredin",
            "philippa_eilhart","yennefer_triss","robert_muldoon","loki"]),
    ("D",  ["dr_sattler","king_arthur","beowulf"]),
]
TIER_RANK  = {f: i for i,(t,fs) in enumerate(TIER_DATA) for f in fs}
TIER_LABEL = {f: t for t,fs in TIER_DATA for f in fs}
TIER_COLORS = {"S":"#f59e0b","A+":"#f97316","A":"#22c55e","B":"#3b82f6","C":"#06b6d4","D":"#94a3b8"}

def get_tier(fid):  return TIER_LABEL.get(fid,"?")
def get_trank(fid): return TIER_RANK.get(fid, None)
TIER_DIFF_SCORE = {0:0.0, 1:0.5, 2:1.0, 3:0.5, 4:0.0, 5:0.0}

FIGHTERS = [
    "king_arthur","alice","medusa","sinbad","robin_hood","bigfoot",
    "robert_muldoon","raptors","dracula","invisible_man","jekyll_hyde",
    "sherlock_holmes","little_red","beowulf","achilles","bloody_mary",
    "sun_wukong","yennenga","luke_cage","ghost_rider","moon_knight",
    "daredevil","elektra","bullseye","dr_sattler","t_rex","houdini",
    "the_genie","ms_marvel","squirrel_girl","cloak_and_dagger",
    "black_panther","black_widow","winter_soldier","she_hulk","spider_man",
    "doctor_strange","nikola_tesla","annie_christmas","the_golden_bat",
    "dr_jill_trent","geralt","ciri","yennefer_triss","philippa_eilhart",
    "eredin","ancient_leshen", "loki", "chupacabra","pandora", "blackbeard"
]

# ── ID Normalizer ─────────────────────────────────────────────────────────
KNOWN_ALIASES = {
    "geralt of rivia": "geralt",
    "the invisible man": "invisible_man"
}
def get_fid(raw_name):
    low = raw_name.lower().strip()
    if low in KNOWN_ALIASES: return KNOWN_ALIASES[low]
    guess = low.replace(" ", "_").replace(".", "").replace("-", "_")
    if guess in FIGHTERS: return guess
    # Fallback to exact match search
    for fid, name in NAME.items():
        if name.lower() == low: return fid
    return guess

# ── Dynamic Match Processor ───────────────────────────────────────────────
played_matches = []
R1_DONE = {}
R1_WINNERS = []

for m in PLAYED_MATCHES_INPUT:
    f1, f2 = get_fid(m["fighter1"]), get_fid(m["fighter2"])
    winner = get_fid(m["winner"])
    loser = f2 if winner == f1 else f1
    
    played_matches.append({
        "f1": f1, "f2": f2, "winner": winner, "player": m["winner_player"]
    })
    R1_DONE[winner] = "winner"
    R1_DONE[loser] = "eliminated"
    R1_WINNERS.append(winner)

remaining = [f for f in FIGHTERS if f not in R1_DONE]

# Calculate exactly how many more R1 matches are needed to reach 32 R2 slots
TOTAL_SLOTS = 32
TOTAL_R1_NEEDED = len(FIGHTERS) - TOTAL_SLOTS
REMAINING_R1_NEEDED = TOTAL_R1_NEEDED - len(played_matches)

# ── Scoring & Optimization Logic ──────────────────────────────────────────
HARD_CUTOFF    = 5.0
DENIAL_PENALTY = -5.0
K_EXP          = 0.04
FAIR_W         = 0.80
TIER_W         = 0.20

def wp(a, b): return matrix.get(a,{}).get(b,-2)
def is_denied(a, b):
    w = wp(a, b)
    return w != -2 and abs(w - 50) > HARD_CUTOFF
def tier_sc(a, b):
    ta, tb = get_trank(a), get_trank(b)
    if ta is None or tb is None: return 0.0
    return TIER_DIFF_SCORE.get(abs(ta - tb), 0.0)
def combined(a, b):
    w = wp(a, b)
    if w == -2: return 0.0
    if abs(w-50) > HARD_CUTOFF: return DENIAL_PENALTY
    return FAIR_W * math.exp(-K_EXP * (w-50)**2) + TIER_W * tier_sc(a, b)

def greedy_match(pool, n_pairs):
    scored = sorted(((combined(a,b), wp(a,b), a, b) for a,b in combinations(pool,2)), reverse=True)
    avail = set(pool); pairs = []
    for sc, w, a, b in scored:
        if len(pairs) == n_pairs: break
        if a in avail and b in avail:
            pairs.append((sc, w, a, b)); avail.discard(a); avail.discard(b)
    return pairs, sorted(avail)

r1_pairs, byes = greedy_match(remaining, REMAINING_R1_NEEDED)

slots_init = (
    [('known', f) for f in R1_WINNERS + byes] +
    [('tbd', a, b) for _,_,a,b in r1_pairs]
)

def fix_known_denials(slots):
    slots = list(slots); fixed = 0; again = True
    while again:
        again = False
        for i in range(0, 32, 2):
            s1, s2 = slots[i], slots[i+1]
            if s1[0]=='known' and s2[0]=='known' and is_denied(s1[1], s2[1]):
                best_j, best_sc = None, -1e18
                for j in range(32):
                    if j in (i, i+1): continue
                    slots[i+1], slots[j] = slots[j], slots[i+1]
                    sc = total_score(slots)
                    if sc > best_sc: best_sc, best_j = sc, j
                    slots[i+1], slots[j] = slots[j], slots[i+1]
                if best_j is not None:
                    slots[i+1], slots[best_j] = slots[best_j], slots[i+1]
                    fixed += 1; again = True; break
    return slots, fixed

def get_dist(slot):
    if slot[0] == 'known': return {slot[1]: 1.0}
    _, a, b = slot; w = wp(a, b)
    return {a:0.5, b:0.5} if w == -2 else {a:w/100, b:(100-w)/100}

def exp_combined(ld, rd): return sum(pl*pr*combined(l,r) for l,pl in ld.items() for r,pr in rd.items())

def merge_dists(ld, rd):
    res = {}
    for l, pl in ld.items():
        for r, pr in rd.items():
            w = wp(l, r); pa = 0.5 if w == -2 else w/100
            res[l] = res.get(l, 0) + pl*pr*pa
            res[r] = res.get(r, 0) + pl*pr*(1-pa)
    return res

def total_score(sl):
    cur = [get_dist(s) for s in sl]; tot = 0.0
    while len(cur) > 1:
        nxt = []
        for i in range(0, len(cur), 2):
            tot += exp_combined(cur[i], cur[i+1]); nxt.append(merge_dists(cur[i], cur[i+1]))
        cur = nxt
    return tot

def optimize(init, n_iter=10000, seed=42):
    random.seed(seed)
    cur = list(init); sc = total_score(cur)
    best, best_sc = list(cur), sc; T = 5.0
    for _ in range(n_iter):
        a, b = random.sample(range(len(cur)), 2)
        cur[a], cur[b] = cur[b], cur[a]
        ns = total_score(cur)
        if ns > sc or random.random() < math.exp((ns-sc)/max(T,1e-9)):
            sc = ns
            if sc > best_sc: best, best_sc = list(cur), sc
        else:
            cur[a], cur[b] = cur[b], cur[a]
        T *= 0.9997
    return best, best_sc

print(f"Generating brackets with {len(played_matches)} played matches...")
opt_slots, _ = optimize(slots_init, n_iter=10000)
opt_slots, _ = fix_known_denials(opt_slots)
r2_matches = [(opt_slots[i], opt_slots[i+1]) for i in range(0, 32, 2)]

# ── Build Bracket JSON ────────────────────────────────────────────────────
def build_bracket():
    bk = {}
    def fi(fid):
        return {"id": fid, "name": n(fid), "tier": get_tier(fid), "tc": TIER_COLORS.get(get_tier(fid), "#6b7280")}
    
    tbd_to_r1 = {}
    played_winners_to_mid = {}
    match_idx = 1
    
    # Process explicitly played matches
    for m in played_matches:
        mid = f"r1_{match_idx}"
        played_winners_to_mid[m["winner"]] = mid
        bk[mid] = {
            "id": mid,
            "label": f"Match {match_idx}",
            "round": 1,
            "top": {"type": "known", **fi(m["f1"])},
            "bot": {"type": "known", **fi(m["f2"])},
            "preset_winner": m["winner"],
            "winner_player": m["player"],
            "meta": {"played_in_advance": True}
        }
        match_idx += 1
        
    # Process dynamically generated remaining R1 matches
    for (sc, w, a, b) in r1_pairs:
        mid = f"r1_{match_idx}"
        tbd_to_r1[(a,b)] = mid; tbd_to_r1[(b,a)] = mid
        wb_ = wp(b,a)
        bk[mid] = {
            "id": mid,
            "label": f"Match {match_idx}",
            "round": 1,
            "top": {"type": "known", **fi(a)},
            "bot": {"type": "known", **fi(b)},
            "preset_winner": None,
            "winner_player": None,
            "meta": {
                "wp": round(w,1) if w!=-2 else None,
                "wp_b": round(wb_,1) if wb_!=-2 else None,
                "score": round(sc,3),
                "tier_diff": abs((get_trank(a) or 0)-(get_trank(b) or 0)),
                "denied": is_denied(a,b)
            }
        }
        match_idx += 1

    # Source mapping for R2
    def slot_of(s):
        if s[0] == 'known':
            fid = s[1]
            if fid in played_winners_to_mid:
                return {"type": "from_match", "src": played_winners_to_mid[fid]}
            return {"type": "known", **fi(fid)}
        _, a, b = s
        src = tbd_to_r1.get((a,b)) or tbd_to_r1.get((b,a))
        return {"type": "from_match", "src": src}

    def meta_for(s1, s2):
        if s1[0]=='known' and s2[0]=='known' and s1[1] not in R1_WINNERS and s2[1] not in R1_WINNERS:
            a, b = s1[1], s2[1]; w_v = wp(a,b); wb_v = wp(b,a)
            return {
                "wp": round(w_v,1) if w_v!=-2 else None,
                "wp_b": round(wb_v,1) if wb_v!=-2 else None,
                "score": round(combined(a,b),3),
                "tier_diff": abs((get_trank(a) or 0)-(get_trank(b) or 0)),
                "denied": is_denied(a,b)
            }
        return None

    # Connect subsequent rounds
    for i, (s1, s2) in enumerate(r2_matches):
        mid = f"r2_{i+1}"
        bk[mid] = {"id": mid, "label": f"R2 Match {i+1}", "round": 2, "top": slot_of(s1), "bot": slot_of(s2), "preset_winner": None, "meta": meta_for(s1,s2)}
        
    for i in range(8):
        mid = f"r3_{i+1}"
        bk[mid] = {"id": mid, "label": f"R3 Match {i+1}", "round": 3, "top": {"type": "from_match", "src": f"r2_{i*2+1}"}, "bot": {"type": "from_match", "src": f"r2_{i*2+2}"}, "preset_winner": None, "meta": None}
        
    for i in range(4):
        mid = f"qf_{i+1}"
        bk[mid] = {"id": mid, "label": f"Quarter-Final {i+1}", "round": 4, "top": {"type": "from_match", "src": f"r3_{i*2+1}"}, "bot": {"type": "from_match", "src": f"r3_{i*2+2}"}, "preset_winner": None, "meta": None}
        
    for i in range(2):
        mid = f"sf_{i+1}"
        bk[mid] = {"id": mid, "label": f"Semi-Final {i+1}", "round": 5, "top": {"type": "from_match", "src": f"qf_{i*2+1}"}, "bot": {"type": "from_match", "src": f"qf_{i*2+2}"}, "preset_winner": None, "meta": None}
        
    bk["final"] = {"id": "final", "label": "⚔ FINAL", "round": 6, "top": {"type": "from_match", "src": "sf_1"}, "bot": {"type": "from_match", "src": "sf_2"}, "preset_winner": None, "meta": None}
    
    return bk

bracket_data = build_bracket()

# Export pure JSON
with open("generated/bracket.json", "w", encoding="utf-8") as f:
    json.dump(bracket_data, f, indent=2, ensure_ascii=False)

print("\nSuccessfully output pure JSON bracket to: generated/bracket.json")