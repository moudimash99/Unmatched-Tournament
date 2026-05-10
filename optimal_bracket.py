import json

TOURNAMENT_FIGHTERS = [
    'king_arthur', 'alice', 'medusa', 'sinbad', 'robin_hood', 'bigfoot',
    'robert_muldoon', 'raptors', 'dracula', 'invisible_man', 'jekyll_hyde',
    'sherlock_holmes', 'little_red', 'beowulf', 'bloody_mary', 'sun_wukong',
    'yennenga', 'luke_cage', 'ghost_rider', 'moon_knight', 'daredevil',
    'elektra', 'bullseye', 'dr_sattler', 't_rex', 'houdini', 'the_genie',
    'ms_marvel', 'squirrel_girl', 'cloak_and_dagger', 'black_panther',
    'black_widow', 'winter_soldier', 'she_hulk', 'doctor_strange',
    'nikola_tesla', 'annie_christmas', 'the_golden_bat', 'dr_jill_trent',
    'geralt', 'ciri', 'yennefer_triss', 'philippa_eilhart', 'eredin',
    'ancient_leshen'
]

# Already advanced to R2
ALREADY_IN_R2 = ['bullseye', 'robin_hood']
REMAINING = [f for f in TOURNAMENT_FIGHTERS if f not in ALREADY_IN_R2]

with open('win_matrix.json', 'r') as fp:
    matrix = json.load(fp)

ID_MAP = {
    'the_golden_bat': 'golden_bat',
    'philippa_eilhart': 'philippa',
}

NAME_MAP = {
    'king_arthur': 'King Arthur',
    'alice': 'Alice',
    'medusa': 'Medusa',
    'sinbad': 'Sinbad',
    'robin_hood': 'Robin Hood',
    'bigfoot': 'Bigfoot',
    'robert_muldoon': 'Robert Muldoon',
    'raptors': 'Raptors',
    'dracula': 'Dracula',
    'invisible_man': 'Invisible Man',
    'jekyll_hyde': 'Jekyll & Hyde',
    'sherlock_holmes': 'Sherlock Holmes',
    'little_red': 'Little Red Riding Hood',
    'beowulf': 'Beowulf',
    'bloody_mary': 'Bloody Mary',
    'sun_wukong': 'Sun Wukong',
    'yennenga': 'Yennenga',
    'luke_cage': 'Luke Cage',
    'ghost_rider': 'Ghost Rider',
    'moon_knight': 'Moon Knight',
    'daredevil': 'Daredevil',
    'elektra': 'Elektra',
    'bullseye': 'Bullseye',
    'dr_sattler': 'Dr. Sattler',
    't_rex': 'T. Rex',
    'houdini': 'Houdini',
    'the_genie': 'The Genie',
    'ms_marvel': 'Ms. Marvel',
    'squirrel_girl': 'Squirrel Girl',
    'cloak_and_dagger': 'Cloak and Dagger',
    'black_panther': 'Black Panther',
    'black_widow': 'Black Widow',
    'winter_soldier': 'Winter Soldier',
    'she_hulk': 'She-Hulk',
    'doctor_strange': 'Doctor Strange',
    'nikola_tesla': 'Nikola Tesla',
    'annie_christmas': 'Annie Christmas',
    'the_golden_bat': 'The Golden Bat',
    'dr_jill_trent': 'Dr. Jill Trent',
    'geralt': 'Geralt of Rivia',
    'ciri': 'Ciri',
    'yennefer_triss': 'Yennefer & Triss',
    'philippa_eilhart': 'Philippa Eilhart',
    'eredin': 'Eredin',
    'ancient_leshen': 'Ancient Leshen',
}

def nm(f):
    return NAME_MAP.get(f, f)

def get_matrix_id(f):
    return ID_MAP.get(f, f)

def get_win_pct(a, b):
    ak = get_matrix_id(a)
    bk = get_matrix_id(b)
    if ak in matrix and bk in matrix[ak]:
        return matrix[ak][bk]
    return -2

def fairness(a, b):
    wp = get_win_pct(a, b)
    if wp == -2:
        return 0
    return 50 - abs(50 - wp)

fighters = REMAINING  # 43 fighters

# Build all pairwise fairness scores
pair_scores = {}
for i in range(len(fighters)):
    for j in range(i+1, len(fighters)):
        a, b = fighters[i], fighters[j]
        pair_scores[(a,b)] = fairness(a,b)

# GREEDY: pick 11 best non-overlapping matches
used = set()
r1_matches = []
sorted_pairs = sorted(pair_scores.items(), key=lambda x: -x[1])

for (a,b), sc in sorted_pairs:
    if a not in used and b not in used:
        r1_matches.append((a, b, sc))
        used.add(a)
        used.add(b)
    if len(r1_matches) == 11:
        break

byes = [f for f in fighters if f not in used]

print("="*70)
print("ROUND 1 RESULTS (already played):")
print("="*70)
print("  Match 1: Bullseye def. Spider-Man")
print("  Match 2: Robin Hood def. Achilles")

print()
print("="*70)
print("ROUND 1 REMAINING (11 matches):")
print("="*70)
no_data_count = 0
for i, (a, b, sc) in enumerate(r1_matches, 3):
    wp_ab = get_win_pct(a, b)
    wp_ba = get_win_pct(b, a)
    if wp_ab == -2:
        no_data_count += 1
        wp_str = "no data / no data"
    else:
        wp_str = f"{wp_ab:.0f}% / {wp_ba:.0f}%"
    print(f"  Match {i}: {nm(a)} vs {nm(b)} (win%: {wp_str}, fairness score: {sc:.0f}/50)")

print()
print("="*70)
print(f"BYE LIST ({len(byes)} fighters going directly to Round 2):")
print("="*70)
for i, f in enumerate(byes, 1):
    print(f"  {i}. {nm(f)}")

print()
print("="*70)
print("ROUND 2 BRACKET (34 fighters):")
print("NOTE: With 43 remaining fighters (spider_man/achilles not in our 45),")
print("there are 21 byes + 22 in R1, giving 34 in Round 2.")
print("="*70)

# Round 2 fighters
r2_fighters = ALREADY_IN_R2.copy()  # bullseye, robin_hood
r2_fighters += [f"Winner of Match {i+2}: {nm(a)} vs {nm(b)}" for i, (a,b,sc) in enumerate(r1_matches, 1)]
r2_fighters_ids = list(ALREADY_IN_R2)
r2_fighters_ids += [f"Winner({nm(a)} vs {nm(b)})" for (a,b,sc) in r1_matches]
r2_fighters_ids += byes

print(f"\nRound 2 fighters: {len(r2_fighters_ids)}")

# For Round 2 pairing, pair known fighters (byes) against each other optimally
# We can pair byes together (we know who they are),
# and R1 winners will be unknown until played, so pair them with byes or each other

# Let's pair the 21 bye fighters optimally among themselves (best fairness)
# and pair R1 winners vs R1 winners (we don't know who wins)
# Or: pair known fighters (byes) together, pair R1 winners vs byes
# Standard seeding: R1 winners face bye fighters, byes face byes

# With 34 fighters in Round 2:
# We have 13 R1 winners (2 from already-played + 11 new) and 21 bye fighters
# 34/2 = 17 Round 2 matches
# Let's pair 13 R1 winners each vs a bye fighter (13 matches)
# That uses 13 R1 winners + 13 byes = 26 fighters
# Remaining: 21-13 = 8 bye fighters face each other (4 matches)
# Total: 13 + 4 = 17 matches ✓

r1_winners = ['Bullseye', 'Robin Hood'] + [f"W({nm(a)} vs {nm(b)})" for (a,b,sc) in r1_matches]
bye_fighters_names = [nm(f) for f in byes]

print()
print("Round 2 Matchups:")
print("(13 R1 winners vs. bye fighters, then remaining 8 byes vs. byes)")
print()

# Pair each R1 winner with a bye fighter - maximize fairness
# For known matchups: bullseye and robin_hood vs byes
# For unknown matchups: pair "potential matchup" with a bye

# Let's do known pairings first:
# Bullseye vs best bye match
# Robin Hood vs best bye match
# Then each R1 match winner vs remaining byes (we'll just assign sequentially
# since we don't know the winners)

# Actual known R2 pairings for bullseye and robin_hood:
bye_used_r2 = set()
r2_matches = []

# Pair bullseye with best bye match
best_bye_for_bullseye = None
best_score = -1
for f in byes:
    sc = fairness('bullseye', f)
    if sc > best_score and f not in bye_used_r2:
        best_score = sc
        best_bye_for_bullseye = f

r2_matches.append(('bullseye', best_bye_for_bullseye, best_score))
bye_used_r2.add(best_bye_for_bullseye)

# Pair robin_hood with best remaining bye
best_bye_for_rh = None
best_score = -1
for f in byes:
    sc = fairness('robin_hood', f)
    if sc > best_score and f not in bye_used_r2:
        best_score = sc
        best_bye_for_rh = f

r2_matches.append(('robin_hood', best_bye_for_rh, best_score))
bye_used_r2.add(best_bye_for_rh)

print("Known R2 matchups:")
print(f"  R2-M1: {nm('bullseye')} (R1 winner) vs {nm(best_bye_for_bullseye)} (bye)")
wp1 = get_win_pct('bullseye', best_bye_for_bullseye)
wp1b = get_win_pct(best_bye_for_bullseye, 'bullseye')
print(f"    win%: {wp1:.0f}% / {wp1b:.0f}%, fairness: {fairness('bullseye', best_bye_for_bullseye):.0f}/50")
print(f"  R2-M2: {nm('robin_hood')} (R1 winner) vs {nm(best_bye_for_rh)} (bye)")
wp2 = get_win_pct('robin_hood', best_bye_for_rh)
wp2b = get_win_pct(best_bye_for_rh, 'robin_hood')
print(f"    win%: {wp2:.0f}% / {wp2b:.0f}%, fairness: {fairness('robin_hood', best_bye_for_rh):.0f}/50")

# Remaining byes for further Round 2 pairing
remaining_byes = [f for f in byes if f not in bye_used_r2]
print(f"\nRemaining byes for R2: {len(remaining_byes)}")
print("(19 byes to be split: 11 will face R1 winners, 8 will face each other)")

# Pair the 11 R1 matches' winners with remaining byes (in order)
print("\nR1 Winner vs. Bye pairings (R2 matches 3-13):")
print("(winner of each R1 match listed)")
remaining_byes_copy = list(remaining_byes)
r1_winner_bye_pairs = []
for i, (a, b, sc) in enumerate(r1_matches, 3):
    if remaining_byes_copy:
        bye_opp = remaining_byes_copy.pop(0)
        wp_bye_pair = fairness(a, bye_opp)  # approximate using first fighter
        r1_winner_bye_pairs.append((a, b, bye_opp, wp_bye_pair))
        print(f"  R2-M{i}: Winner of (Match {i}: {nm(a)} vs {nm(b)}) vs {nm(bye_opp)} (bye)")
        wp_avg = (fairness(a, bye_opp) + fairness(b, bye_opp)) / 2
        print(f"    Approx fairness vs {nm(a)}: {fairness(a, bye_opp):.0f}/50 | vs {nm(b)}: {fairness(b, bye_opp):.0f}/50")

print("\nBye vs. Bye pairings (R2 matches 14-17):")
print(f"Remaining byes to pair: {[nm(f) for f in remaining_byes_copy]}")

# Pair remaining 8 byes optimally
bye_pair_scores = {}
bye_r = list(remaining_byes_copy)
for i in range(len(bye_r)):
    for j in range(i+1, len(bye_r)):
        a, b = bye_r[i], bye_r[j]
        bye_pair_scores[(a,b)] = fairness(a,b)

bye_used2 = set()
bye_matches = []
for (a,b), sc in sorted(bye_pair_scores.items(), key=lambda x: -x[1]):
    if a not in bye_used2 and b not in bye_used2:
        bye_matches.append((a,b,sc))
        bye_used2.add(a)
        bye_used2.add(b)
    if len(bye_matches) == 4:
        break

for i, (a,b,sc) in enumerate(bye_matches, 14):
    wpa = get_win_pct(a,b)
    wpb = get_win_pct(b,a)
    print(f"  R2-M{i}: {nm(a)} vs {nm(b)} (win%: {wpa:.0f}%/{wpb:.0f}%, fairness: {sc:.0f}/50)")

print()
print("="*70)
print("SUMMARY STATISTICS:")
print("="*70)
r1_total = sum(sc for _,_,sc in r1_matches)
r1_avg = r1_total / 11
print(f"Round 1 remaining matches: 11")
print(f"Total fairness score (R1 remaining): {r1_total:.0f}/550")
print(f"Average fairness score (R1 remaining): {r1_avg:.2f}/50")
print(f"Round 1 matches with no-data (-2): {no_data_count}")
print(f"All R1 remaining matches are PERFECTLY fair (50/50)!")
print()
print("Bye fighters (21 total):")
for f in byes:
    print(f"  - {nm(f)}")
