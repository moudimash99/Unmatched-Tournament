"""
Generates tournament_a.html, tournament_b1.html, tournament_b2.html.
Appended after tournament_head.py in tournament.py.
"""
import json as _json

r1_scores  = [sc for sc, *_ in r1_pairs]
r2_matches = [(opt_slots[i], opt_slots[i+1]) for i in range(0, 32, 2)]

# ── Bracket JSON ──────────────────────────────────────────────────────────────
def build_bracket():
    tbd = {}
    for i, (sc, w, a, b) in enumerate(r1_pairs):
        mid = f"r1_{i+3}"
        tbd[(a, b)] = mid; tbd[(b, a)] = mid

    def fi(fid):
        return {"type": "known", "id": fid, "name": n(fid),
                "tier": get_tier(fid), "tc": TIER_COLORS.get(get_tier(fid), "#6b7280")}

    def slot(s):
        if s[0] == 'known':
            fid = s[1]
            if fid == 'bullseye':   return {"type": "from_match", "src": "r1_1"}
            if fid == 'robin_hood': return {"type": "from_match", "src": "r1_2"}
            return {"type": "known", **fi(fid)}
        _, a, b = s
        return {"type": "from_match", "src": tbd.get((a, b)) or tbd.get((b, a))}

    def meta2(s1, s2):
        if s1[0]=='known' and s2[0]=='known' and s1[1] not in R1_WINNERS and s2[1] not in R1_WINNERS:
            a, b = s1[1], s2[1]; wv = wp(a, b); wbv = wp(b, a)
            return {"wp": round(wv,1) if wv!=-2 else None,
                    "wp_b": round(wbv,1) if wbv!=-2 else None,
                    "score": round(combined(a,b), 3),
                    "tier_diff": abs((get_trank(a) or 0)-(get_trank(b) or 0)),
                    "denied": is_denied(a, b)}
        return None

    bk = {}
    bk["r1_1"] = {"id":"r1_1","label":"Match 1","round":1,"top":fi("bullseye"),"bot":fi("spider_man"),
        "preset_winner":"bullseye","meta":{"wp":None,"wp_b":None,"score":None,"tier_diff":1,"denied":False}}
    bk["r1_2"] = {"id":"r1_2","label":"Match 2","round":1,"top":fi("robin_hood"),"bot":fi("achilles"),
        "preset_winner":"robin_hood","meta":{"wp":None,"wp_b":None,"score":None,"tier_diff":2,"denied":False}}
    for i, (sc, w, a, b) in enumerate(r1_pairs):
        mid = f"r1_{i+3}"; wbv = wp(b, a); td = abs((get_trank(a) or 0)-(get_trank(b) or 0))
        bk[mid] = {"id":mid,"label":f"Match {i+3}","round":1,"top":fi(a),"bot":fi(b),"preset_winner":None,
            "meta":{"wp":round(w,1) if w!=-2 else None,"wp_b":round(wbv,1) if wbv!=-2 else None,
                    "score":round(sc,3),"tier_diff":td,"denied":is_denied(a,b)}}
    for i, (s1, s2) in enumerate(r2_matches):
        mid = f"r2_{i+1}"
        bk[mid] = {"id":mid,"label":f"R2-{i+1}","round":2,
            "top":slot(s1),"bot":slot(s2),"preset_winner":None,"meta":meta2(s1,s2)}
    for pfx, rnd, spfx, sz in [("r3",3,"r2",8),("qf",4,"r3",4),("sf",5,"qf",2)]:
        for i in range(sz):
            mid = f"{pfx}_{i+1}"
            bk[mid] = {"id":mid,"label":f"{pfx.upper()}-{i+1}","round":rnd,
                "top":{"type":"from_match","src":f"{spfx}_{i*2+1}"},
                "bot":{"type":"from_match","src":f"{spfx}_{i*2+2}"},"preset_winner":None,"meta":None}
    bk["final"] = {"id":"final","label":"FINAL","round":6,
        "top":{"type":"from_match","src":"sf_1"},
        "bot":{"type":"from_match","src":"sf_2"},"preset_winner":None,"meta":None}
    return bk

BK      = build_bracket()
BK_JSON = _json.dumps(BK, ensure_ascii=False)

def tbadge(fid):
    t = get_tier(fid); c = TIER_COLORS.get(t, "#6b7280")
    dark = t in ("S","A+","A")
    return f'<span class="tb" style="background:{c};color:{"#000" if dark else "#fff"}">{t}</span>'

bye_chips = "".join(f'<div class="bye-chip">{tbadge(f)} {n(f)}</div>' for f in byes)
r1d = ["r1_1","r1_2"]
r1r = [f"r1_{i}" for i in range(3, 16)]
r2s = [f"r2_{i}" for i in range(1, 17)]
r3s = [f"r3_{i}" for i in range(1, 9)]
qfs = [f"qf_{i}" for i in range(1, 5)]
sfs = ["sf_1","sf_2"]

def ph(ids):
    return "".join(f'<div id="mc-{m}" class="mc"></div>' for m in ids)

# ── Shared base CSS ───────────────────────────────────────────────────────────
BASE_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0f172a;color:#e2e8f0}
header{background:linear-gradient(135deg,#1e293b,#0f172a);border-bottom:3px solid #f59e0b;padding:1.1rem 2rem;text-align:center}
h1{font-size:1.45rem;font-weight:800;color:#f59e0b;text-transform:uppercase;letter-spacing:.05em}
.sb{display:flex;justify-content:center;align-items:stretch;margin:.8rem auto 0;max-width:360px;border-radius:10px;overflow:hidden;border:2px solid #334155}
.panel{flex:1;padding:.65rem .9rem;text-align:center;background:#1e293b;transition:background .2s}
.panel.lead{background:#1c2e4a}
.ptag{font-size:.58rem;color:#64748b;text-transform:uppercase;letter-spacing:.1em}
.pname{font-size:.82rem;font-weight:700;margin:.08rem 0}
.pscore{font-size:2rem;font-weight:900;line-height:1.1}
.p1c{color:#3b82f6}.p2c{color:#f97316}
.sb-vs{display:flex;align-items:center;padding:0 .45rem;background:#1e293b;color:#475569;font-size:.58rem;font-weight:800}
.reset-btn{display:block;margin:.32rem auto 0;font-size:.64rem;color:#475569;background:none;border:1px solid #2d3748;border-radius:4px;padding:.16rem .52rem;cursor:pointer}
.reset-btn:hover{color:#ef4444;border-color:#ef4444}
.mc{background:#1e293b;border:1px solid #2d3748;border-radius:8px;padding:.65rem .8rem;transition:box-shadow .15s}
.mc:hover{box-shadow:0 3px 10px rgba(0,0,0,.4)}
.mc.done{border-color:#1d4ed844}.mc.picking{border-color:#f59e0b55}
.mc.denied{border-color:#ef444444;background:#7f1d1d11}.mc.dim{opacity:.45}
.lrow{display:flex;align-items:center;gap:.22rem;flex-wrap:wrap;margin-bottom:.35rem}
.ltext{font-size:.58rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:#64748b}
.sc-b{font-size:.54rem;padding:.05rem .26rem;border-radius:999px;font-weight:700}
.done-b{font-size:.54rem;padding:.05rem .26rem;border-radius:999px;background:#22c55e22;color:#22c55e;border:1px solid #22c55e44;font-weight:700}
.mf-name{font-size:.8rem;font-weight:600;line-height:1.3;display:flex;align-items:baseline;flex-wrap:wrap;gap:.18rem}
.mf-name.won{color:#fbbf24}.mf-name.lost{color:#475569;text-decoration:line-through}
.mf-name.tbd{color:#64748b;font-style:italic;font-size:.72rem}
.mf-name.possible{flex-direction:column;align-items:flex-start;gap:.1rem}
.poss-label{font-size:.55rem;color:#475569;font-style:normal;font-weight:600}
.poss-chip{font-size:.68rem;color:#94a3b8;font-style:normal;display:inline-flex;align-items:center;gap:.16rem}
.vs-txt{font-size:.53rem;font-weight:800;color:#475569;letter-spacing:.1em;padding:.04rem 0}
.tb{font-size:.5rem;padding:.04rem .22rem;border-radius:3px;font-weight:800;flex-shrink:0}
.win-btns{display:grid;grid-template-columns:1fr 1fr;gap:.28rem;margin-top:.35rem}
.win-btn{padding:.3rem .18rem;border-radius:6px;border:1.5px solid #334155;background:#0f172a;color:#e2e8f0;font-size:.67rem;font-weight:600;cursor:pointer;line-height:1.2;transition:border-color .15s,background .15s}
.win-btn:hover{border-color:#f59e0b;background:#1e293b}
.pick-label{font-size:.62rem;color:#94a3b8;margin:.38rem 0 .24rem;text-align:center}
.player-btns{display:grid;grid-template-columns:1fr 1fr;gap:.28rem}
.pb-p1{padding:.28rem;border-radius:5px;border:none;background:#3b82f6;color:#fff;font-size:.68rem;font-weight:700;cursor:pointer}
.pb-p2{padding:.28rem;border-radius:5px;border:none;background:#f97316;color:#fff;font-size:.68rem;font-weight:700;cursor:pointer}
.pb-p1:hover,.pb-p2:hover{opacity:.85}
.result-row{display:flex;align-items:center;justify-content:space-between;margin-top:.26rem}
.player-tag{font-size:.65rem;font-weight:700}
.undo-btn{font-size:.56rem;color:#475569;background:none;border:1px solid #2d3748;border-radius:3px;padding:.12rem .38rem;cursor:pointer}
.undo-btn:hover{color:#ef4444;border-color:#ef4444}
.fbar-wrap{margin-top:.3rem;height:3px;background:#1e3a5f;border-radius:2px;overflow:hidden}
.fbar-fill{height:100%;border-radius:2px}
.fbar-pct{font-size:.53rem;color:#475569;margin-top:.12rem;text-align:right}
.bye-list{display:flex;flex-wrap:wrap;gap:.3rem}
.bye-chip{background:#1e293b;border:1px solid #2d3748;border-radius:999px;padding:.16rem .55rem;font-size:.7rem;color:#cbd5e1;display:flex;align-items:center;gap:.2rem}
footer{text-align:center;color:#334155;font-size:.59rem;padding:.7rem;border-top:1px solid #1e293b;margin-top:.7rem}
.score-help{margin:.45rem auto 0;max-width:620px;font-size:.62rem;line-height:1.35;color:#94a3b8}
"""

SB_HTML = """
  <div class="sb">
    <div class="panel" id="p1panel"><div class="ptag">P1</div><div class="pname">Ahmad</div><div class="pscore p1c" id="p1score">0</div></div>
    <div class="sb-vs">VS</div>
    <div class="panel" id="p2panel"><div class="ptag">P2</div><div class="pname">Mohammad</div><div class="pscore p2c" id="p2score">0</div></div>
  </div>
  <button class="reset-btn" onclick="resetAll()">↺ reset</button>
  <p class="score-help">Scoring guide: score badge = matchup quality, and the bar always shows win % (top fighter vs bottom fighter). Green is near 50/50, yellow/red means less balanced.</p>
"""

# ── Shared JS (two modes: full possible-fighters OR compact labels) ────────────
def make_js(compact_tbd=False):
    tbd_logic = r"""
    // Compact: just show source match label
    function fname(f, side) {
      if (!f) {
        const slot = side==="top" ? m.top : m.bot;
        if (!slot || slot.type!=="from_match") return `<span class="mf-name tbd">TBD</span>`;
        const src = BK[slot.src];
        return `<span class="mf-name tbd">W: ${src ? src.label : slot.src}</span>`;
      }
      const isW=w&&f.id===w, isL=w&&f.id!==w;
      return `<span class="mf-name ${isW?"won":isL?"lost":""}">${f.name} ${tbHtml(f)}${isW?" ♛":""}</span>`;
    }
    """ if compact_tbd else r"""
    // Full: show all possible fighters recursively
    function allPossible(slot, d) {
      d = d || 0; if (!slot || d > 6) return [];
      if (slot.type==="known") { const f=resolve(slot); return f?[f]:[]; }
      const w2 = getWinner(slot.src); if (w2) return [dig(slot.src, w2)];
      const src = BK[slot.src]; if (!src) return [];
      const seen=new Set(), out=[];
      [...allPossible(src.top,d+1),...allPossible(src.bot,d+1)].forEach(f=>{
        if(!seen.has(f.id)){seen.add(f.id);out.push(f);}
      });
      return out;
    }
    function fname(f, side) {
      if (!f) {
        const poss = allPossible(side==="top" ? m.top : m.bot);
        if (!poss.length) return `<span class="mf-name tbd">⏳ TBD</span>`;
        if (poss.length <= 2)
          return `<span class="mf-name tbd">W: ${poss.map(p=>p.name+" "+tbHtml(p)).join(" <em>vs</em> ")}</span>`;
        return `<span class="mf-name tbd possible">
          <span class="poss-label">Possible (${poss.length}):</span>
          ${poss.map(p=>`<span class="poss-chip">${p.name} ${tbHtml(p)}</span>`).join("")}
        </span>`;
      }
      const isW=w&&f.id===w, isL=w&&f.id!==w;
      return `<span class="mf-name ${isW?"won":isL?"lost":""}">${f.name} ${tbHtml(f)}${isW?" ♛":""}</span>`;
    }
    """

    return (r"""
const BK = __BK__;
const PNAME={P1:"Ahmad",P2:"Mohammad"}, PC={P1:"#3b82f6",P2:"#f97316"};
let ST={};try{ST=JSON.parse(localStorage.getItem("um_v4")||"{}");}catch(e){}
const WP_CACHE={},WP_PENDING=new Set();
function save(){localStorage.setItem("um_v4",JSON.stringify(ST));}
function loadPairWp(a,b){
  const k=`${a}|${b}`,rk=`${b}|${a}`,m=WP_CACHE[k]||WP_CACHE[rk];
  if(m||WP_PENDING.has(k))return m||null;
  WP_PENDING.add(k);
  fetch(`/api/win-pct?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`).then(r=>r.ok?r.json():null).then(d=>{
    if(d&&d.wp!=null&&d.wp_b!=null){
      const r1=Math.round(d.wp*10)/10,r2=Math.round(d.wp_b*10)/10;
      const wm={wp:r1,wp_b:r2,denied:Math.abs(r1-50)>5};
      WP_CACHE[k]=wm;WP_CACHE[rk]={wp:r2,wp_b:r1,denied:Math.abs(r2-50)>5};renderAll();
    }
  }).catch(()=>{}).finally(()=>WP_PENDING.delete(k));
  return null;
}

function getWinner(mid){const m=BK[mid];if(!m)return null;if(m.preset_winner)return m.preset_winner;return ST[mid]?.winner||null;}
function resolve(slot){if(!slot)return null;if(slot.type==="known")return{id:slot.id,name:slot.name,tier:slot.tier,tc:slot.tc};const w=getWinner(slot.src);if(!w)return null;return dig(slot.src,w);}
function dig(mid,fid){const m=BK[mid];if(!m)return{id:fid,name:fid,tier:"?",tc:"#6b7280"};const t=resolve(m.top);if(t&&t.id===fid)return t;const b=resolve(m.bot);if(b&&b.id===fid)return b;return{id:fid,name:fid,tier:"?",tc:"#6b7280"};}
function pickWinner(mid,side){const m=BK[mid];if(!m||m.preset_winner)return;const f=side==="top"?resolve(m.top):resolve(m.bot);if(!f)return;ST[mid]={winner:f.id,side};save();renderAll();}
function pickPlayer(mid,player){const m=BK[mid];if(!m)return;if(!ST[mid])ST[mid]={winner:m.preset_winner,side:"top"};ST[mid].player=player;save();renderAll();}
function undoMatch(mid){const m=BK[mid];if(!m||m.preset_winner)return;delete ST[mid];cascade(mid);save();renderAll();}
function cascade(mid){Object.keys(BK).forEach(k=>{const m=BK[k];if((m.top?.src===mid||m.bot?.src===mid)&&ST[k]){delete ST[k];cascade(k);}});}
function resetAll(){if(!confirm("Reset all results?"))return;ST={};save();renderAll();}
function tbHtml(f){if(!f)return"";const dark=["S","A+","A"].includes(f.tier);return`<span class="tb" style="background:${f.tc||"#6b7280"};color:${dark?"#000":"#fff"}">${f.tier||"?"}</span>`;}
function updateSB(){let p1=0,p2=0;Object.values(ST).forEach(r=>{if(r.player==="P1")p1++;else if(r.player==="P2")p2++;});document.getElementById("p1score").textContent=p1;document.getElementById("p2score").textContent=p2;document.getElementById("p1panel").classList.toggle("lead",p1>p2);document.getElementById("p2panel").classList.toggle("lead",p2>p1);}

function renderCard(mid){
  const el=document.getElementById("mc-"+mid);if(!el)return;
  const m=BK[mid],tf=resolve(m.top),bf=resolve(m.bot);
  const w=getWinner(mid),res=ST[mid],isPreset=!!m.preset_winner;
  const bothKnown=!!(tf&&bf),hasWin=!!w,hasPl=!!(res?.player||(isPreset&&ST[mid]?.player));
  const waiting=hasWin&&!hasPl,complete=hasWin&&hasPl;
  const meta=m.meta;
  const liveMeta=(bothKnown&&tf?.id&&bf?.id)?loadPairWp(tf.id,bf.id):null;
  const shownMeta=liveMeta||meta;
  el.className="mc"+(complete?" done":"")+(waiting?" picking":"")+(shownMeta?.denied?" denied":"")+(!bothKnown&&!isPreset?" dim":"");

  let lrow=`<div class="lrow"><span class="ltext">${m.label}</span>`;
  if(meta?.score!=null){const s=meta.score,c=s>=.75?"#22c55e":s>=.55?"#84cc16":s>=.35?"#eab308":"#f97316";lrow+=`<span class="sc-b" style="background:${c};color:#000">${s.toFixed(2)}</span>`;}
  if(shownMeta?.denied)lrow+=`<span class="sc-b" style="background:#ef4444;color:#fff">⚠</span>`;
  if(complete)lrow+=`<span class="done-b">✓</span>`;
  lrow+="</div>";

  __FNAME_LOGIC__

  let fbar="";
  if(shownMeta?.wp!=null){const d=Math.abs(shownMeta.wp-50),c=d<=2?"#22c55e":d<=3.5?"#84cc16":d<=5?"#eab308":"#ef4444";fbar=`<div class="fbar-wrap"><div class="fbar-fill" style="width:${shownMeta.wp}%;background:${c}"></div></div><div class="fbar-pct">${shownMeta.wp}% vs ${shownMeta.wp_b}%</div>`;}

  let action="";
  if(complete){
    const pl=res?.player,pc=pl?PC[pl]:"#94a3b8";
    if(isPreset&&!pl){action=`<p class="pick-label">Who played ${dig(mid,w).name}?</p><div class="player-btns"><button class="pb-p1" onclick="pickPlayer('${mid}','P1')">Ahmad</button><button class="pb-p2" onclick="pickPlayer('${mid}','P2')">Mohammad</button></div>`;}
    else{action=`<div class="result-row"><span class="player-tag" style="color:${pc}">🎮 ${pl?PNAME[pl]+" ("+pl+")":"—"}</span>${!isPreset?`<button class="undo-btn" onclick="undoMatch('${mid}')">↩</button>`:""}</div>`;}
  }else if(waiting){action=`<p class="pick-label">♛ ${dig(mid,w).name} — who played?</p><div class="player-btns"><button class="pb-p1" onclick="pickPlayer('${mid}','P1')">Ahmad</button><button class="pb-p2" onclick="pickPlayer('${mid}','P2')">Mohammad</button></div>`;}
  else if(bothKnown&&!isPreset){action=`<div class="win-btns"><button class="win-btn" onclick="pickWinner('${mid}','top')">${tf.name} wins</button><button class="win-btn" onclick="pickWinner('${mid}','bot')">${bf.name} wins</button></div>`;}
  else if(isPreset&&!hasWin){action=`<p class="pick-label">♛ ${dig(mid,m.preset_winner).name} won — who played?</p><div class="player-btns"><button class="pb-p1" onclick="pickPlayer('${mid}','P1')">Ahmad</button><button class="pb-p2" onclick="pickPlayer('${mid}','P2')">Mohammad</button></div>`;}

  el.innerHTML=lrow+fname(tf,"top")+`<div class="vs-txt">${complete?"def.":"vs"}</div>`+fname(bf,"bot")+fbar+action;
}
function renderAll(){Object.keys(BK).forEach(renderCard);updateSB();}
renderAll();
""").replace("__BK__", BK_JSON).replace("__FNAME_LOGIC__", tbd_logic)


# ═══════════════════════════════════════════════════════════════════════════════
# OPTION A — card grid
# ═══════════════════════════════════════════════════════════════════════════════
CSS_A = """
main{max-width:1300px;margin:0 auto;padding:1.2rem 2rem}
section{margin-bottom:1.6rem}
h2{font-size:.9rem;font-weight:700;color:#f59e0b;text-transform:uppercase;letter-spacing:.08em;border-left:4px solid #f59e0b;padding-left:.55rem;margin-bottom:.6rem}
.sublabel{font-size:.58rem;text-transform:uppercase;letter-spacing:.1em;color:#64748b;margin:.6rem 0 .35rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:.55rem}
"""
HTML_A = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tournament — Cards</title><style>{BASE_CSS}{CSS_A}</style></head><body>
<header><h1>⚔ Unmatched Tournament — Card View</h1>{SB_HTML}</header>
<main>
<section><h2>Round 1</h2>
  <div class="sublabel">Already played</div><div class="grid">{ph(r1d)}</div>
  <div class="sublabel">Remaining — 13 matches</div><div class="grid">{ph(r1r)}</div>
</section>
<section><h2>Byes to Round 2</h2><div class="bye-list">{bye_chips}</div></section>
<section><h2>Round 2</h2><div class="grid">{ph(r2s)}</div></section>
<section><h2>Round 3</h2><div class="grid">{ph(r3s)}</div></section>
<section><h2>Quarter-Finals</h2><div class="grid">{ph(qfs)}</div></section>
<section><h2>Semi-Finals</h2><div class="grid">{ph(sfs)}</div></section>
<section><h2>⚔ Final</h2><div class="grid">{ph(["final"])}</div></section>
</main>
<footer>Card view — possible fighters shown for deep rounds</footer>
<script>{make_js(compact_tbd=False)}</script></body></html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# BRACKET helpers (shared by B1 and B2)
# ═══════════════════════════════════════════════════════════════════════════════
SIDEBAR_CSS = """
.page{display:flex;height:calc(100vh - 100px);min-height:550px}
.sidebar{width:255px;flex-shrink:0;overflow-y:auto;border-right:1px solid #1e293b;padding:.85rem 1rem}
.sidebar h2{font-size:.8rem;font-weight:700;color:#f59e0b;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #f59e0b;padding-left:.45rem;margin-bottom:.5rem}
.sidebar .sublabel{font-size:.56rem;text-transform:uppercase;letter-spacing:.09em;color:#64748b;margin:.5rem 0 .3rem}
.sidebar .mc{margin-bottom:.35rem}
"""

SIDEBAR_HTML = f"""
  <div class="sidebar">
    <h2>Round 1</h2>
    <div class="sublabel">Already played</div>
    {ph(r1d)}
    <div class="sublabel">Remaining — 13 matches</div>
    {ph(r1r)}
    <div class="sublabel">Byes (17)</div>
    <div class="bye-list" style="margin-bottom:.5rem">{bye_chips}</div>
  </div>
"""


# ═══════════════════════════════════════════════════════════════════════════════
# OPTION B1 — Bracket with compact "W of X" placeholders
#   Uniform card height → flex alignment works correctly
# ═══════════════════════════════════════════════════════════════════════════════
# Structure: each column is a flex column.
# Each bgroup has flex:1, so n groups share column height equally.
# R2 has 8 groups → each = 1/8 column.
# R3 has 4 groups → each = 1/4 column = 2 × R2 group → lines align.
# bgroup::before draws the vertical bracket (25%→75% of group height).
# bgroup::after draws the outgoing horizontal line (at 50%).
# bslot::before draws the incoming line.

GAP = 24  # px gap between bracket columns

B1_BRACKET_CSS = f"""
.bracket-wrap{{flex:1;overflow:auto;padding:1rem 1.2rem}}
.bracket{{display:flex;gap:{GAP}px;align-items:stretch;min-height:700px;height:100%}}
.bcol{{display:flex;flex-direction:column;width:195px;flex-shrink:0}}
.bcol-label{{font-size:.66rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:#f59e0b;text-align:center;padding:.3rem 0 .4rem;border-bottom:1px solid #1e3a5f;flex-shrink:0}}
/* each group gets equal share of column height */
.bgroup{{flex:1;display:flex;flex-direction:column;position:relative}}
/* vertical bracket line: from center of top slot to center of bottom slot */
.bgroup::before{{content:'';position:absolute;right:0;top:25%;height:50%;width:2px;background:#2d3748;pointer-events:none}}
/* outgoing horizontal line at midpoint of group */
.bgroup::after{{content:'';position:absolute;right:-{GAP}px;top:calc(50% - 1px);width:{GAP}px;height:2px;background:#2d3748;pointer-events:none}}
/* each match slot */
.bslot{{flex:1;display:flex;align-items:center;padding:3px 0;position:relative;min-width:0}}
/* incoming line on non-first columns */
.has-in .bslot::before{{content:'';position:absolute;left:-{GAP}px;top:calc(50% - 1px);width:{GAP}px;height:2px;background:#2d3748;pointer-events:none}}
/* final column */
.bfinal{{flex:1;display:flex;align-items:center;padding:3px 0;position:relative}}
.bfinal::before{{content:'';position:absolute;left:-{GAP}px;top:calc(50% - 1px);width:{GAP}px;height:2px;background:#2d3748;pointer-events:none}}
.bslot .mc, .bfinal .mc{{width:100%;overflow:hidden}}
"""

def b1_bracket_cols():
    rounds = [
        ("R2",  r2s,       8, False),
        ("R3",  r3s,       4, True),
        ("QF",  qfs,       2, True),
        ("SF",  sfs,       1, True),
        ("⚔",  ["final"], 0, True),
    ]
    cols = []
    for label, ids, n_grp, has_in in rounds:
        in_cls = " has-in" if has_in else ""
        lbl = f'<div class="bcol-label">{label}</div>'
        if n_grp == 0:
            inner = f'<div class="bfinal"><div id="mc-{ids[0]}" class="mc"></div></div>'
        else:
            groups = []
            for gi in range(n_grp):
                pair = ids[gi*2 : gi*2+2]
                slots = "".join(f'<div class="bslot{in_cls}"><div id="mc-{m}" class="mc"></div></div>' for m in pair)
                groups.append(f'<div class="bgroup">{slots}</div>')
            inner = "".join(groups)
        cols.append(f'<div class="bcol">{lbl}{inner}</div>')
    return "".join(cols)

HTML_B1 = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tournament — Bracket B1</title>
<style>{BASE_CSS}{SIDEBAR_CSS}{B1_BRACKET_CSS}</style></head><body>
<header><h1>⚔ Unmatched Tournament — Bracket (compact labels)</h1>{SB_HTML}</header>
<div class="page">
  {SIDEBAR_HTML}
  <div class="bracket-wrap">
    <div class="bracket">{b1_bracket_cols()}</div>
  </div>
</div>
<footer>B1: compact "W of X" placeholders · flex alignment · same state as other views</footer>
<script>{make_js(compact_tbd=True)}</script></body></html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# OPTION B2 — HTML table with rowspan
#
# Why tables work perfectly:
#   • rowspan=2 for R3, rowspan=4 for QF, rowspan=8 for SF, rowspan=16 for Final
#   • The browser handles vertical alignment natively — no CSS tricks needed
#   • Bracket lines: ::before on spanning cells at top:25% height:50%
#     This is ALWAYS correct because each spanning cell gets exactly 2 inputs
#     (top half and bottom half), whose centers are always at 25% and 75%
#   • Horizontal arms: ::after on every source cell at top:calc(50%-1px)
#   • border-spacing creates a gap the arms/lines live in
# ═══════════════════════════════════════════════════════════════════════════════

TBGAP = 20  # px gap between bracket table columns (used by border-spacing)

B2_TABLE_CSS = (
  ".bracket-wrap{flex:1;overflow:auto;padding:1.5rem}"
  ".bracket-table{border-collapse:separate;border-spacing:20px 10px;table-layout:fixed}"
  ".bc{position:relative;vertical-align:middle;padding:0;width:205px}"
  ".bc-r2::after,.bc-r3::after,.bc-qf::after,.bc-sf::after{"
    "content:'';position:absolute;"
    "right:-20px;top:calc(50% - 1px);width:20px;height:2px;"
    "background:#2d3748;pointer-events:none}"
  ".bc-r3::before,.bc-qf::before,.bc-sf::before,.bc-final::before{"
    "content:'';position:absolute;"
    "left:-20px;width:2px;background:#2d3748;pointer-events:none}"
  ".bc-r3::before{top:23.9130%;height:52.1739%;}"
  ".bc-qf::before{top:24.4681%;height:51.0638%;}"
  ".bc-sf::before{top:24.7368%;height:50.5263%;}"
  ".bc-final::before{top:24.8691%;height:50.2618%;}"
  ".bc-r2{min-height:110px;}"
  ".bracket-col-hdr{font-size:.66rem;font-weight:700;text-transform:uppercase;"
    "letter-spacing:.09em;color:#f59e0b;text-align:center;"
    "padding:.3rem 0;border-bottom:1px solid #1e3a5f}"
)


def b2_table():
    N = 16  # number of R2 matches

    # Header row
    labels = ["R2","R3","QF","SF","⚔ Final"]
    hdr = "".join(f'<th class="bracket-col-hdr">{l}</th>' for l in labels)

    rows = ""
    for row in range(1, N+1):
        cells = ""

        # R2 — every row
        r2_id = r2s[row - 1]
        cells += f'<td class="bc bc-r2"><div id="mc-{r2_id}" class="mc"></div></td>'

        # R3 — rows 1,3,5,…  rowspan=2
        if row % 2 == 1:
            r3_id = r3s[(row - 1) // 2]
            cells += f'<td class="bc bc-r3" rowspan="2"><div id="mc-{r3_id}" class="mc"></div></td>'

        # QF — rows 1,5,9,13  rowspan=4
        if row % 4 == 1:
            qf_id = qfs[(row - 1) // 4]
            cells += f'<td class="bc bc-qf" rowspan="4"><div id="mc-{qf_id}" class="mc"></div></td>'

        # SF — rows 1,9  rowspan=8
        if row % 8 == 1:
            sf_id = sfs[(row - 1) // 8]
            cells += f'<td class="bc bc-sf" rowspan="8"><div id="mc-{sf_id}" class="mc"></div></td>'

        # Final — row 1 only  rowspan=16
        if row == 1:
            cells += f'<td class="bc bc-final" rowspan="16"><div id="mc-final" class="mc"></div></td>'

        rows += f"<tr>{cells}</tr>\n"

    return f'<table class="bracket-table"><thead><tr>{hdr}</tr></thead><tbody>{rows}</tbody></table>'

HTML_B2 = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tournament — Bracket</title>
<style>{BASE_CSS}{SIDEBAR_CSS}{B2_TABLE_CSS}</style></head><body>
<header><h1>&#9876; Unmatched Tournament &#8212; Bracket View</h1>{SB_HTML}</header>
<div class="page">
  {SIDEBAR_HTML}
  <div class="bracket-wrap">
    {b2_table()}
  </div>
</div>
<footer>Table bracket: rowspan handles alignment natively &#183; same localStorage state as card view</footer>
<script>{make_js(compact_tbd=False)}</script></body></html>"""


# ── Write all three ───────────────────────────────────────────────────────────
for fname_out, html in [("tournament_a.html", HTML_A),
                         ("tournament_b1.html", HTML_B1),
                         ("tournament_b2.html", HTML_B2)]:
  with open(f"generated/{fname_out}", "w", encoding="utf-8") as f:
        f.write(html)
  print(f"Written: generated/{fname_out}")
