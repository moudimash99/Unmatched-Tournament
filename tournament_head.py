import json, sys, random, math
from itertools import combinations
sys.stdout.reconfigure(encoding="utf-8")

# ── Load ───────────────────────────────────────────────────────────────────
with open("merged_win_pct.json") as f:
    matrix = json.load(f)

with open("fighters.json") as f:
    NAME = {f["id"]: f["name"] for f in json.load(f)["fighters"]}
NAME.update({"the_golden_bat":"The Golden Bat","philippa_eilhart":"Philippa Eilhart","eredin":"Eredin Breacc Glas"})
def n(fid): return NAME.get(fid, fid.replace("_"," ").title())

# ── Tier data ──────────────────────────────────────────────────────────────
TIER_DATA = [
    ("S",  ["ciri","medusa","sherlock_holmes","elektra","achilles"]),
    ("A+", ["ancient_leshen","sun_wukong","yennenga","bigfoot"]),
    ("A",  ["daredevil","bullseye","little_red","sinbad","geralt","robin_hood"]),
    ("B",  ["t_rex","alice","dracula","she_hulk","spider_man","nikola_tesla",
            "dr_jill_trent","annie_christmas","the_golden_bat","winter_soldier",
            "black_widow","bloody_mary"]),
    ("C",  ["luke_cage","raptors","invisible_man","jekyll_hyde","moon_knight",
            "ghost_rider","houdini","the_genie","ms_marvel","squirrel_girl",
            "cloak_and_dagger","black_panther","doctor_strange","eredin",
            "philippa_eilhart","yennefer_triss","robert_muldoon"]),
    ("D",  ["dr_sattler","king_arthur","beowulf"]),
]
TIER_RANK  = {f: i for i,(t,fs) in enumerate(TIER_DATA) for f in fs}
TIER_LABEL = {f: t for t,fs in TIER_DATA for f in fs}
TIER_COLORS = {"S":"#f59e0b","A+":"#f97316","A":"#22c55e","B":"#3b82f6","C":"#06b6d4","D":"#94a3b8"}

def get_tier(fid):  return TIER_LABEL.get(fid,"?")
def get_trank(fid): return TIER_RANK.get(fid, None)

TIER_DIFF_SCORE = {0:0.0, 1:0.5, 2:1.0, 3:0.5, 4:0.0, 5:0.0}

# ── Fighters (47 total, excl. skipped) ────────────────────────────────────
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
    "eredin","ancient_leshen",
]
# 47 → next power of 2 = 64 → 17 byes, 15 R1 matches (2 done → 13 left)

R1_DONE    = {"bullseye":"winner","spider_man":"eliminated","robin_hood":"winner","achilles":"eliminated"}
R1_WINNERS = [f for f,r in R1_DONE.items() if r=="winner"]
remaining  = [f for f in FIGHTERS if f not in R1_DONE]  # 43

# ── Scoring parameters ─────────────────────────────────────────────────────
HARD_CUTOFF    = 5.0   # |win% - 50| > this → denied
DENIAL_PENALTY = -5.0  # active penalty so SA/greedy never choose denied pairs
K_EXP          = 0.04  # exp(-K * dev^2): dev=0→1.0, dev=2→0.85, dev=5→0.37
FAIR_W         = 0.80
TIER_W         = 0.20

def wp(a, b): return matrix.get(a,{}).get(b,-2)

def is_denied(a, b):
    w = wp(a, b)
    return w != -2 and abs(w - 50) > HARD_CUTOFF

def fair_exp(a, b):
    w = wp(a, b)
    if w == -2: return 0.0
    dev = abs(w - 50)
    return 0.0 if dev > HARD_CUTOFF else math.exp(-K_EXP * dev * dev)

def tier_sc(a, b):
    ta, tb = get_trank(a), get_trank(b)
    if ta is None or tb is None: return 0.0
    return TIER_DIFF_SCORE.get(abs(ta - tb), 0.0)

def combined(a, b):
    """DENIAL_PENALTY if outside ±5% cutoff; else 0.80*fairness_exp + 0.20*tier."""
    w = wp(a, b)
    if w == -2:   return 0.0           # unknown → neutral
    if abs(w-50) > HARD_CUTOFF: return DENIAL_PENALTY  # confirmed bad → punish
    return FAIR_W * math.exp(-K_EXP * (w-50)**2) + TIER_W * tier_sc(a, b)

# ── Post-SA hard fix: swap any denied known-vs-known R2 pairs ──────────────
def fix_known_denials(slots):
    """Guarantee no known-vs-known bracket pair is denied.
    For each denied pair, find the single swap that maximises total_score."""
    slots = list(slots)
    fixed = 0
    again = True
    while again:
        again = False
        for i in range(0, 32, 2):
            s1, s2 = slots[i], slots[i+1]
            if s1[0]=='known' and s2[0]=='known' and is_denied(s1[1], s2[1]):
                # Find best swap of slot i+1 with any other slot
                best_j, best_sc = None, -1e18
                for j in range(32):
                    if j in (i, i+1): continue
                    slots[i+1], slots[j] = slots[j], slots[i+1]
                    sc = total_score(slots)
                    if sc > best_sc:
                        best_sc, best_j = sc, j
                    slots[i+1], slots[j] = slots[j], slots[i+1]
                if best_j is not None:
                    slots[i+1], slots[best_j] = slots[best_j], slots[i+1]
                    fixed += 1; again = True; break
    return slots, fixed

# ── Greedy matching ────────────────────────────────────────────────────────
def greedy_match(pool, n_pairs):
    scored = sorted(
        ((combined(a,b), wp(a,b), a, b) for a,b in combinations(pool,2)),
        reverse=True
    )
    avail = set(pool); pairs = []
    for sc, w, a, b in scored:
        if len(pairs) == n_pairs: break
        if a in avail and b in avail:
            pairs.append((sc, w, a, b)); avail.discard(a); avail.discard(b)
    return pairs, sorted(avail)

# ── R1 pairings ────────────────────────────────────────────────────────────
r1_pairs, byes = greedy_match(remaining, 13)

# ── Build 32 R2 slots ──────────────────────────────────────────────────────
slots_init = (
    [('known', f) for f in R1_WINNERS + byes] +
    [('tbd', a, b) for _,_,a,b in r1_pairs]
)
assert len(slots_init) == 32

# ── Probability propagation ────────────────────────────────────────────────
def get_dist(slot):
    if slot[0] == 'known': return {slot[1]: 1.0}
    _, a, b = slot
    w = wp(a, b)
    return {a:0.5, b:0.5} if w == -2 else {a:w/100, b:(100-w)/100}

def merge_dists(ld, rd):
    res = {}
    for l, pl in ld.items():
        for r, pr in rd.items():
            w = wp(l, r); pa = 0.5 if w == -2 else w/100
            res[l] = res.get(l, 0) + pl*pr*pa
            res[r] = res.get(r, 0) + pl*pr*(1-pa)
    return res

def exp_combined(ld, rd):
    """Expected combined score for a match given two probability distributions."""
    return sum(pl*pr*combined(l,r) for l,pl in ld.items() for r,pr in rd.items())

def total_score(sl):
    dists = [get_dist(s) for s in sl]; tot = 0.0; cur = dists
    while len(cur) > 1:
        nxt = []
        for i in range(0, len(cur), 2):
            tot += exp_combined(cur[i], cur[i+1]); nxt.append(merge_dists(cur[i], cur[i+1]))
        cur = nxt
    return tot

def round_scores(sl):
    dists = [get_dist(s) for s in sl]; rounds = []; cur = dists
    while len(cur) > 1:
        rs = 0; nxt = []
        for i in range(0, len(cur), 2):
            rs += exp_combined(cur[i], cur[i+1]); nxt.append(merge_dists(cur[i], cur[i+1]))
        rounds.append(rs); cur = nxt
    return rounds

# ── Simulated annealing ────────────────────────────────────────────────────
def optimize(init, n_iter=10000, seed=42):
    random.seed(seed)
    cur = list(init); sc = total_score(cur)
    best, best_sc = list(cur), sc
    T = 5.0
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

print("Scoring naive bracket ...", flush=True)
naive_sc  = total_score(slots_init)
naive_rds = round_scores(slots_init)
print(f"  Naive:     {naive_sc:.3f}")
print("Optimising bracket (R2-R6) ...", flush=True)
opt_slots, opt_sc = optimize(slots_init, n_iter=10000)
print(f"  SA result: {opt_sc:.3f}  (+{opt_sc-naive_sc:.3f})")
print("Fixing any remaining denied known pairs ...", flush=True)
opt_slots, n_fixed = fix_known_denials(opt_slots)
opt_sc  = total_score(opt_slots)
opt_rds = round_scores(opt_slots)
print(f"  Fixed {n_fixed} pair(s). Final: {opt_sc:.3f}\n")

# ── Display helpers ────────────────────────────────────────────────────────
def slot_label(s):
    if s[0] == 'known': return n(s[1])
    _, a, b = s
    return f"Winner of: {n(a)} vs {n(b)}"

def match_detail(s1, s2):
    """Returns (win_pct_a, win_pct_b, combined_score, denied, is_tbd)."""
    if s1[0] != 'known' or s2[0] != 'known': return None, None, None, False, True
    a, b = s1[1], s2[1]
    w = wp(a, b); wb = wp(b, a); sc = combined(a, b)
    denied = (w != -2 and abs(w-50) > HARD_CUTOFF)
    return w, wb, sc, denied, False

r2_matches = [(opt_slots[i], opt_slots[i+1]) for i in range(0, 32, 2)]

def build_later_rounds(n_r2=16):
    rounds = []; prev_size = n_r2
    while prev_size > 1:
        rounds.append([(i, i+1) for i in range(0, prev_size, 2)]); prev_size //= 2
    return rounds

later_rounds = build_later_rounds(16)
rnames   = ["R3","QF","SF","Final"]
rnd_full = ["Round 3 — Round of 16","Quarter-Finals","Semi-Finals","Final"]

# ── Text output ────────────────────────────────────────────────────────────
print("="*72)
print("  UNMATCHED SINGLES TOURNAMENT")
print("  Scoring: 80% exp-fairness (hard cutoff ±5%) + 20% tier diversity")
print("="*72)

print("\n-- R1 DONE --")
print("  Match  1: [A] Bullseye     def. [B] Spider-Man")
print("  Match  2: [A] Robin Hood   def. [S] Achilles")

r1_denied = 0
print("\n-- R1 REMAINING (13 matches) --")
for i,(sc,w,a,b) in enumerate(r1_pairs,3):
    wb = wp(b,a); ta,tb = get_tier(a),get_tier(b)
    diff = abs((get_trank(a) or 0)-(get_trank(b) or 0))
    if w == -2:
        det = "no data"
    elif abs(w-50) > HARD_CUTOFF:
        det = f"DENIED {w:.0f}%/{wb:.0f}% ⚠"; r1_denied += 1
    else:
        det = f"{w:.1f}%/{wb:.1f}%  tier-diff={diff}  score={sc:.3f}"
    print(f"  Match {i:2d}: [{ta}] {n(a):<26s} vs [{tb}] {n(b):<26s}  [{det}]")

print(f"\n-- BYES ({len(byes)}) --")
for f in byes: print(f"  [{get_tier(f)}] {n(f)}")

print("\n-- R2 (optimised R2-R6) --")
for i,(s1,s2) in enumerate(r2_matches,1):
    w,wb,sc_v,denied,tbd = match_detail(s1,s2)
    l1,l2 = slot_label(s1),slot_label(s2)
    if tbd: det="TBD"
    elif w==-2: det="no data"
    elif denied: det=f"DENIED {w:.0f}%/{wb:.0f}% ⚠"
    else:
        diff=abs((get_trank(s1[1]) or 0)-(get_trank(s2[1]) or 0))
        det=f"{w:.1f}%/{wb:.1f}%  tier-diff={diff}  score={sc_v:.3f}"
    print(f"  R2-{i:02d}: {l1:<38s} vs {l2:<38s}  [{det}]")

print("\n-- LATER ROUNDS --")
prev = [f"R2-{i:02d}" for i in range(1,17)]
for ri,rnd in enumerate(later_rounds):
    nxt=[]
    for li,(l,r) in enumerate(rnd):
        lbl=f"{rnames[ri]}-{li+1:02d}"
        print(f"  {lbl}: W({prev[l]}) vs W({prev[r]})")
        nxt.append(lbl)
    prev=nxt

r1_scores=[sc for sc,*_ in r1_pairs]
print(f"\n-- STATS --")
print(f"  R1: avg score={sum(r1_scores)/len(r1_scores):.3f}  denied={r1_denied}/13")
for lab,sc in zip(["R2","R3","QF","SF","Final"],opt_rds): print(f"  {lab}: {sc:.3f}")
print(f"  Total: {opt_sc:.3f}  (naive: {naive_sc:.3f}  +{opt_sc-naive_sc:.3f})")

# ── Build bracket JSON for interactive HTML ────────────────────────────────
def build_bracket():
    tbd_to_r1 = {}
    for i,(sc,w,a,b) in enumerate(r1_pairs):
        mid = f"r1_{i+3}"
        tbd_to_r1[(a,b)] = mid; tbd_to_r1[(b,a)] = mid

    def fi(fid):
        return {"id":fid,"name":n(fid),"tier":get_tier(fid),"tc":TIER_COLORS.get(get_tier(fid),"#6b7280")}

    def slot_of(s):
        if s[0]=='known':
            fid=s[1]
            if fid=='bullseye':   return {"type":"from_match","src":"r1_1"}
            if fid=='robin_hood': return {"type":"from_match","src":"r1_2"}
            return {"type":"known",**fi(fid)}
        _,a,b=s
        src=tbd_to_r1.get((a,b)) or tbd_to_r1.get((b,a))
        return {"type":"from_match","src":src}

    def meta_for(s1,s2):
        if s1[0]=='known' and s2[0]=='known' and s1[1] not in R1_WINNERS and s2[1] not in R1_WINNERS:
            a,b=s1[1],s2[1]; w_v=wp(a,b); wb_v=wp(b,a)
            return {"wp":round(w_v,1) if w_v!=-2 else None,
                    "wp_b":round(wb_v,1) if wb_v!=-2 else None,
                    "score":round(combined(a,b),3),
                    "tier_diff":abs((get_trank(a) or 0)-(get_trank(b) or 0)),
                    "denied":is_denied(a,b)}
        return None

    bk={}
    bk["r1_1"]={"id":"r1_1","label":"Match 1","round":1,
        "top":fi("bullseye"),"bot":fi("spider_man"),
        "preset_winner":"bullseye",
        "meta":{"wp":None,"wp_b":None,"score":None,"tier_diff":1,"denied":False}}
    bk["r1_2"]={"id":"r1_2","label":"Match 2","round":1,
        "top":fi("robin_hood"),"bot":fi("achilles"),
        "preset_winner":"robin_hood",
        "meta":{"wp":None,"wp_b":None,"score":None,"tier_diff":2,"denied":False}}
    for i,(sc,w,a,b) in enumerate(r1_pairs):
        mid=f"r1_{i+3}"; wb_=wp(b,a)
        bk[mid]={"id":mid,"label":f"Match {i+3}","round":1,
            "top":fi(a),"bot":fi(b),"preset_winner":None,
            "meta":{"wp":round(w,1) if w!=-2 else None,
                    "wp_b":round(wb_,1) if wb_!=-2 else None,
                    "score":round(sc,3),
                    "tier_diff":abs((get_trank(a) or 0)-(get_trank(b) or 0)),
                    "denied":is_denied(a,b)}}
    for i,(s1,s2) in enumerate(r2_matches):
        mid=f"r2_{i+1}"
        bk[mid]={"id":mid,"label":f"R2 Match {i+1}","round":2,
            "top":slot_of(s1),"bot":slot_of(s2),
            "preset_winner":None,"meta":meta_for(s1,s2)}
    for i in range(8):
        mid=f"r3_{i+1}"
        bk[mid]={"id":mid,"label":f"R3 Match {i+1}","round":3,
            "top":{"type":"from_match","src":f"r2_{i*2+1}"},
            "bot":{"type":"from_match","src":f"r2_{i*2+2}"},
            "preset_winner":None,"meta":None}
    for i in range(4):
        mid=f"qf_{i+1}"
        bk[mid]={"id":mid,"label":f"Quarter-Final {i+1}","round":4,
            "top":{"type":"from_match","src":f"r3_{i*2+1}"},
            "bot":{"type":"from_match","src":f"r3_{i*2+2}"},
            "preset_winner":None,"meta":None}
    for i in range(2):
        mid=f"sf_{i+1}"
        bk[mid]={"id":mid,"label":f"Semi-Final {i+1}","round":5,
            "top":{"type":"from_match","src":f"qf_{i*2+1}"},
            "bot":{"type":"from_match","src":f"qf_{i*2+2}"},
            "preset_winner":None,"meta":None}
    bk["final"]={"id":"final","label":"⚔ FINAL","round":6,
        "top":{"type":"from_match","src":"sf_1"},
        "bot":{"type":"from_match","src":"sf_2"},
        "preset_winner":None,"meta":None}
    return bk

bracket_data  = build_bracket()
bracket_json  = json.dumps(bracket_data, ensure_ascii=False)

# Helper for bye chips (static HTML)
def tier_badge_html(fid):
    t=get_tier(fid); col=TIER_COLORS.get(t,"#6b7280")
    return f'<span class="tbadge" style="background:{col};color:{"#000" if t in ("S","A+","A") else "#fff"}">{t}</span>'

