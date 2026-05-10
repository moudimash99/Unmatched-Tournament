
# ─────────────────────────────────────────────────────────────────────────────
# Interactive HTML generation  (2-click flow: pick winner → pick player)
# ─────────────────────────────────────────────────────────────────────────────
import json as _json

r1_scores   = [sc for sc,*_ in r1_pairs]
r1_denied   = sum(1 for sc,w,*_ in r1_pairs if w!=-2 and abs(w-50)>HARD_CUTOFF)
avg_r1      = sum(r1_scores)/len(r1_scores)
r2_matches  = [(opt_slots[i], opt_slots[i+1]) for i in range(0,32,2)]

# ── Build bracket JSON ────────────────────────────────────────────────────────
def build_bracket():
    tbd_to_r1={}
    for i,(sc,w,a,b) in enumerate(r1_pairs):
        mid=f"r1_{i+3}"; tbd_to_r1[(a,b)]=mid; tbd_to_r1[(b,a)]=mid

    def fi(fid):
        return {"type":"known","id":fid,"name":n(fid),"tier":get_tier(fid),"tc":TIER_COLORS.get(get_tier(fid),"#6b7280")}

    def slot_of(s):
        if s[0]=='known':
            fid=s[1]
            if fid=='bullseye':   return {"type":"from_match","src":"r1_1"}
            if fid=='robin_hood': return {"type":"from_match","src":"r1_2"}
            return {"type":"known",**fi(fid)}
        _,a,b=s
        return {"type":"from_match","src":tbd_to_r1.get((a,b)) or tbd_to_r1.get((b,a))}

    def r2meta(s1,s2):
        if s1[0]=='known' and s2[0]=='known' and s1[1] not in R1_WINNERS and s2[1] not in R1_WINNERS:
            a,b=s1[1],s2[1]; wv=wp(a,b); wbv=wp(b,a)
            return {"wp":round(wv,1) if wv!=-2 else None,"wp_b":round(wbv,1) if wbv!=-2 else None,
                    "score":round(combined(a,b),3),
                    "tier_diff":abs((get_trank(a) or 0)-(get_trank(b) or 0)),
                    "denied":is_denied(a,b)}
        return None

    bk={}
    bk["r1_1"]={"id":"r1_1","label":"Match 1","round":1,"top":fi("bullseye"),"bot":fi("spider_man"),
        "preset_winner":"bullseye","meta":{"wp":None,"wp_b":None,"score":None,"tier_diff":1,"denied":False}}
    bk["r1_2"]={"id":"r1_2","label":"Match 2","round":1,"top":fi("robin_hood"),"bot":fi("achilles"),
        "preset_winner":"robin_hood","meta":{"wp":None,"wp_b":None,"score":None,"tier_diff":2,"denied":False}}
    for i,(sc,w,a,b) in enumerate(r1_pairs):
        mid=f"r1_{i+3}"; wbv=wp(b,a); td=abs((get_trank(a) or 0)-(get_trank(b) or 0))
        bk[mid]={"id":mid,"label":f"Match {i+3}","round":1,"top":fi(a),"bot":fi(b),"preset_winner":None,
            "meta":{"wp":round(w,1) if w!=-2 else None,"wp_b":round(wbv,1) if wbv!=-2 else None,
                    "score":round(sc,3),"tier_diff":td,"denied":is_denied(a,b)}}
    for i,(s1,s2) in enumerate(r2_matches):
        mid=f"r2_{i+1}"
        bk[mid]={"id":mid,"label":f"R2 Match {i+1}","round":2,
            "top":slot_of(s1),"bot":slot_of(s2),"preset_winner":None,"meta":r2meta(s1,s2)}
    for rnd,size,name in [(3,8,"R3"),(4,4,"QF"),(5,2,"SF")]:
        prev="r2" if rnd==3 else ("r3" if rnd==4 else "qf")
        pfx={"r3":"r3","qf":"r3","sf":"qf"}; pfx={"r2":"r2","r3":"r3","qf":"qf","sf":"sf"}
        src_pfx={"3":"r2","4":"r3","5":"qf"}[str(rnd)]
        for i in range(size):
            mid=f"{'r3' if rnd==3 else 'qf' if rnd==4 else 'sf'}_{i+1}"
            bk[mid]={"id":mid,"label":f"{name} Match {i+1}","round":rnd,
                "top":{"type":"from_match","src":f"{src_pfx}_{i*2+1}"},
                "bot":{"type":"from_match","src":f"{src_pfx}_{i*2+2}"},"preset_winner":None,"meta":None}
    bk["final"]={"id":"final","label":"THE FINAL","round":6,
        "top":{"type":"from_match","src":"sf_1"},"bot":{"type":"from_match","src":"sf_2"},
        "preset_winner":None,"meta":None}
    return bk

BK      = build_bracket()
BK_JSON = _json.dumps(BK, ensure_ascii=False)

def tbadge(fid):
    t=get_tier(fid); c=TIER_COLORS.get(t,"#6b7280")
    return f'<span class="tb" style="background:{c};color:{"#000" if t in ("S","A+","A") else "#fff"}">{t}</span>'

bye_chips = "".join(f'<div class="bye-chip">{tbadge(f)} {n(f)}</div>' for f in byes)
r1_done_ids   = ["r1_1","r1_2"]
r1_remain_ids = [f"r1_{i}" for i in range(3,16)]
r2_ids  = [f"r2_{i}" for i in range(1,17)]
r3_ids  = [f"r3_{i}" for i in range(1,9)]
qf_ids  = [f"qf_{i}" for i in range(1,5)]
sf_ids  = ["sf_1","sf_2"]

def placeholders(ids):
    return "".join(f'<div id="mc-{m}" class="mc"></div>' for m in ids)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Unmatched Tournament</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0f172a;color:#e2e8f0}

/* header */
header{background:linear-gradient(135deg,#1e293b,#0f172a);border-bottom:3px solid #f59e0b;padding:1.4rem 2rem;text-align:center}
h1{font-size:1.7rem;font-weight:800;color:#f59e0b;text-transform:uppercase;letter-spacing:.05em}

/* scoreboard */
.sb{display:flex;justify-content:center;align-items:stretch;gap:0;margin:1rem auto 0;max-width:420px;border-radius:14px;overflow:hidden;border:2px solid #334155}
.panel{flex:1;padding:.9rem 1.2rem;text-align:center;background:#1e293b;transition:background .2s}
.panel.lead{background:#1c2e4a}
.panel .ptag{font-size:.65rem;color:#64748b;text-transform:uppercase;letter-spacing:.1em}
.panel .pname{font-size:.95rem;font-weight:700;margin:.15rem 0}
.panel .pscore{font-size:2.6rem;font-weight:900;line-height:1.1}
.sb-vs{display:flex;align-items:center;padding:0 .6rem;background:#1e293b;color:#475569;font-size:.65rem;font-weight:800}
.p1c{color:#3b82f6}.p2c{color:#f97316}
.reset-btn{display:block;margin:.5rem auto 0;font-size:.7rem;color:#475569;background:none;border:1px solid #2d3748;border-radius:6px;padding:.22rem .65rem;cursor:pointer}
.reset-btn:hover{color:#ef4444;border-color:#ef4444}

/* layout */
main{max-width:1300px;margin:0 auto;padding:1.5rem 2rem}
section{margin-bottom:2rem}
h2{font-size:1.05rem;font-weight:700;color:#f59e0b;text-transform:uppercase;letter-spacing:.08em;border-left:4px solid #f59e0b;padding-left:.65rem;margin-bottom:.75rem}
.sublabel{font-size:.65rem;text-transform:uppercase;letter-spacing:.1em;color:#64748b;margin:.75rem 0 .45rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(255px,1fr));gap:.7rem}

/* card */
.mc{background:#1e293b;border:1px solid #2d3748;border-radius:11px;padding:.8rem .95rem;transition:box-shadow .15s}
.mc:hover{box-shadow:0 4px 16px rgba(0,0,0,.4)}
.mc.done{border-color:#1d4ed844}
.mc.picking{border-color:#f59e0b55;background:#1e293b}
.mc.denied{border-color:#ef444444;background:#7f1d1d11}
.mc.dim{opacity:.55}

/* label row */
.lrow{display:flex;align-items:center;gap:.3rem;flex-wrap:wrap;margin-bottom:.5rem}
.ltext{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:#64748b}
.sc-b{font-size:.6rem;padding:.08rem .32rem;border-radius:999px;font-weight:700}
.td-b{font-size:.58rem;padding:.08rem .3rem;border-radius:4px;border:1px solid;font-weight:700}
.done-b{font-size:.6rem;padding:.08rem .32rem;border-radius:999px;background:#22c55e22;color:#22c55e;border:1px solid #22c55e44;font-weight:700}

/* fighters display — vertical layout so long names always fit */
.match-fighters{display:flex;flex-direction:column;gap:.05rem;margin-bottom:.5rem}
.mf-name{font-size:.88rem;font-weight:600;line-height:1.35;display:flex;align-items:center;flex-wrap:wrap;gap:.25rem}
.mf-name.won{color:#fbbf24}.mf-name.lost{color:#475569;text-decoration:line-through}
.mf-name.tbd{color:#64748b;font-style:italic;font-size:.78rem}
.vs-txt{font-size:.6rem;font-weight:800;color:#475569;letter-spacing:.1em;padding:.1rem 0;text-align:center}
.tb{font-size:.56rem;padding:.07rem .28rem;border-radius:4px;font-weight:800;flex-shrink:0}

/* win buttons — 2 big buttons, one per fighter */
.win-btns{display:grid;grid-template-columns:1fr 1fr;gap:.4rem;margin-top:.45rem}
.win-btn{padding:.42rem .3rem;border-radius:8px;border:1.5px solid #334155;background:#0f172a;color:#e2e8f0;font-size:.75rem;font-weight:600;cursor:pointer;text-align:center;line-height:1.25;transition:border-color .15s,background .15s}
.win-btn:hover{border-color:#f59e0b;background:#1e293b}

/* player pick row — appears after winner chosen */
.pick-label{font-size:.7rem;color:#94a3b8;margin:.5rem 0 .3rem;text-align:center}
.player-btns{display:grid;grid-template-columns:1fr 1fr;gap:.4rem}
.pb-p1{padding:.38rem;border-radius:7px;border:none;background:#3b82f6;color:#fff;font-size:.78rem;font-weight:700;cursor:pointer;transition:opacity .15s}
.pb-p2{padding:.38rem;border-radius:7px;border:none;background:#f97316;color:#fff;font-size:.78rem;font-weight:700;cursor:pointer;transition:opacity .15s}
.pb-p1:hover,.pb-p2:hover{opacity:.85}

/* result display */
.result-row{display:flex;align-items:center;justify-content:space-between;margin-top:.35rem}
.player-tag{font-size:.72rem;font-weight:700}
.undo-btn{font-size:.62rem;color:#475569;background:none;border:1px solid #2d3748;border-radius:5px;padding:.18rem .5rem;cursor:pointer;transition:color .15s}
.undo-btn:hover{color:#ef4444;border-color:#ef4444}

/* fairness bar */
.fbar-wrap{margin-top:.4rem;height:4px;background:#1e3a5f;border-radius:2px;overflow:hidden}
.fbar-fill{height:100%;border-radius:2px}
.fbar-pct{font-size:.58rem;color:#475569;margin-top:.18rem;text-align:right}

/* byes */
.bye-list{display:flex;flex-wrap:wrap;gap:.38rem}
.bye-chip{background:#1e293b;border:1px solid #2d3748;border-radius:999px;padding:.22rem .7rem;font-size:.76rem;color:#cbd5e1;display:flex;align-items:center;gap:.28rem}

footer{text-align:center;color:#334155;font-size:.65rem;padding:1rem;border-top:1px solid #1e293b;margin-top:1rem}
</style>
</head>
<body>
<header>
  <h1>&#9876; Unmatched Singles Tournament</h1>

  <div class="sb">
    <div class="panel" id="p1panel">
      <div class="ptag">P1</div>
      <div class="pname">Ahmad</div>
      <div class="pscore p1c" id="p1score">0</div>
    </div>
    <div class="sb-vs">VS</div>
    <div class="panel" id="p2panel">
      <div class="ptag">P2</div>
      <div class="pname">Mohammad</div>
      <div class="pscore p2c" id="p2score">0</div>
    </div>
  </div>
  <button class="reset-btn" onclick="resetAll()">&#8635; reset all</button>
</header>
<main>

<section>
  <h2>Round 1</h2>
  <div class="sublabel">Already played</div>
  <div class="grid">""" + placeholders(r1_done_ids) + """</div>
  <div class="sublabel">Remaining — 13 matches</div>
  <div class="grid">""" + placeholders(r1_remain_ids) + """</div>
</section>

<section>
  <h2>Byes to Round 2 — 17 fighters</h2>
  <div class="bye-list">""" + bye_chips + """</div>
</section>

<section>
  <h2>Round 2</h2>
  <div class="grid">""" + placeholders(r2_ids) + """</div>
</section>

<section>
  <h2>Round 3 — Round of 16</h2>
  <div class="grid">""" + placeholders(r3_ids) + """</div>
</section>

<section>
  <h2>Quarter-Finals</h2>
  <div class="grid">""" + placeholders(qf_ids) + """</div>
</section>

<section>
  <h2>Semi-Finals</h2>
  <div class="grid">""" + placeholders(sf_ids) + """</div>
</section>

<section>
  <h2>&#9876; Final</h2>
  <div class="grid">""" + placeholders(["final"]) + """</div>
</section>

</main>
<footer>Fairness scoring: exp(&#8722;0.04&#215;dev&sup2;) &bull; Hard cutoff &plusmn;5% &bull; 20% tier diversity &bull; SA optimised R2&#8211;R6</footer>

<script>
const BK = """ + BK_JSON + """;
const PNAME = {P1:"Ahmad", P2:"Mohammad"};
const PC    = {P1:"#3b82f6", P2:"#f97316"};

// state[mid] = {winner: id, side: "top"|"bot"} or {winner, side, player: "P1"|"P2"}
let ST = {};
try { ST = JSON.parse(localStorage.getItem("um_v2") || "{}"); } catch(e){}
function save(){ localStorage.setItem("um_v2", JSON.stringify(ST)); }

// ── Resolution ──────────────────────────────────────────────────────────────
function getWinner(mid){
  const m = BK[mid]; if(!m) return null;
  if(m.preset_winner) return m.preset_winner;
  return ST[mid]?.winner || null;
}
function resolve(slot){
  if(!slot) return null;
  if(slot.type==="known") return {id:slot.id, name:slot.name, tier:slot.tier, tc:slot.tc};
  const w = getWinner(slot.src); if(!w) return null;
  return dig(slot.src, w);
}
function dig(mid, fid){
  const m = BK[mid]; if(!m) return {id:fid, name:fid, tier:"?", tc:"#6b7280"};
  const t = resolve(m.top); if(t && t.id===fid) return t;
  const b = resolve(m.bot); if(b && b.id===fid) return b;
  return {id:fid, name:fid, tier:"?", tc:"#6b7280"};
}

// ── Actions ─────────────────────────────────────────────────────────────────
function pickWinner(mid, side){
  const m = BK[mid]; if(!m || m.preset_winner) return;
  const f = side==="top" ? resolve(m.top) : resolve(m.bot);
  if(!f) return;
  ST[mid] = {winner: f.id, side};
  save(); renderAll();
}
function pickPlayer(mid, player){
  if(!ST[mid] && BK[mid]?.preset_winner){
    ST[mid] = {winner: BK[mid].preset_winner, side:"top"};
  }
  if(!ST[mid]) return;
  ST[mid].player = player;
  save(); renderAll();
}
function undoMatch(mid){
  const m = BK[mid]; if(!m || m.preset_winner) return;
  delete ST[mid];
  // cascade: invalidate any match that depends on this result
  Object.keys(BK).forEach(k=>{
    const bm = BK[k];
    if((bm.top?.src===mid || bm.bot?.src===mid) && ST[k]){
      delete ST[k]; undoCascade(k);
    }
  });
  save(); renderAll();
}
function undoCascade(mid){
  Object.keys(BK).forEach(k=>{
    const bm=BK[k];
    if((bm.top?.src===mid||bm.bot?.src===mid)&&ST[k]){delete ST[k];undoCascade(k);}
  });
}
function resetAll(){
  if(!confirm("Reset all recorded results?")) return;
  ST={}; save(); renderAll();
}

// ── Render ───────────────────────────────────────────────────────────────────
function tbHtml(f){
  if(!f) return "";
  const dark=["S","A+","A"].includes(f.tier);
  return `<span class="tb" style="background:${f.tc||"#6b7280"};color:${dark?"#000":"#fff"}">${f.tier||"?"}</span>`;
}

// For a TBD slot, get the two possible fighters from the source match
function pendingFighters(slot){
  if(!slot || slot.type!=="from_match") return null;
  const src=BK[slot.src]; if(!src) return null;
  const tf=resolve(src.top), bf=resolve(src.bot);
  return {tf, bf};
}

function renderCard(mid){
  const el = document.getElementById("mc-"+mid); if(!el) return;
  const m  = BK[mid];
  const tf = resolve(m.top);
  const bf = resolve(m.bot);
  const w  = getWinner(mid);
  const res= ST[mid];
  const isPreset = !!m.preset_winner;

  // States
  const bothKnown  = !!(tf && bf);
  const winnerPicked = !!w;
  const playerPicked = !!(res?.player || (isPreset && ST[mid]?.player));
  const waitingPlayer = winnerPicked && !playerPicked;
  const complete   = winnerPicked && playerPicked;

  // Card class
  el.className = "mc" +
    (complete ? " done" : "") +
    (waitingPlayer ? " picking" : "") +
    (m.meta?.denied ? " denied" : "") +
    (!bothKnown && !isPreset ? " dim" : "");

  // ── Label row ──
  const meta = m.meta;
  let lrow = `<div class="lrow"><span class="ltext">${m.label}</span>`;
  if(meta?.score!=null){
    const s=meta.score, sc=s>=.75?"#22c55e":s>=.55?"#84cc16":s>=.35?"#eab308":"#f97316";
    lrow+=`<span class="sc-b" style="background:${sc};color:#000">${s.toFixed(2)}</span>`;
  }
  if(meta?.denied) lrow+=`<span class="sc-b" style="background:#ef4444;color:#fff">&#9888; Denied</span>`;
  if(meta?.tier_diff!=null){
    const d=meta.tier_diff,[tc,tl]=d===2?["#22c55e","&#9733;&#9733;Δ2"]:d===1||d===3?["#f59e0b",`&#9733;Δ${d}`]:["#ef444488",`Δ${d}`];
    lrow+=`<span class="td-b" style="border-color:${tc};color:${tc}">${tl}</span>`;
  }
  if(complete) lrow+=`<span class="done-b">&#10003; Done</span>`;
  lrow+="</div>";

  // ── Fighters line ──
  function fname(f, side){
    if(!f){
      const slot = side==="top" ? m.top : m.bot;
      const pend = pendingFighters(slot);
      if(pend && pend.tf && pend.bf){
        return `<span class="mf-name tbd">W: ${pend.tf.name} ${tbHtml(pend.tf)} vs ${pend.bf.name} ${tbHtml(pend.bf)}</span>`;
      }
      return `<span class="mf-name tbd">&#8987; TBD</span>`;
    }
    const isW=w&&f.id===w, isL=w&&f.id!==w;
    return `<span class="mf-name ${isW?"won":isL?"lost":""}">${f.name} ${tbHtml(f)}${isW?" &#9812;":""}</span>`;
  }
  const fline = `<div class="match-fighters">
    ${fname(tf,"top")}
    <div class="vs-txt">${complete?"def.":"vs"}</div>
    ${fname(bf,"bot")}
  </div>`;

  // ── Fairness bar ──
  let fbar="";
  if(meta?.wp!=null && !meta.denied){
    const d=Math.abs(meta.wp-50),bc=d<=2?"#22c55e":d<=3.5?"#84cc16":d<=5?"#eab308":"#ef4444";
    fbar=`<div class="fbar-wrap"><div class="fbar-fill" style="width:${meta.wp}%;background:${bc}"></div></div>
          <div class="fbar-pct">${meta.wp}% vs ${meta.wp_b}%</div>`;
  }

  // ── Action area ──
  let action="";

  if(complete){
    // Show who won and player tag + undo
    const pl=res?.player; const pc=pl?PC[pl]:"#94a3b8";
    const ptxt=pl?`&#127918; ${PNAME[pl]} (${pl})`:"&#128100; player?";
    action=`<div class="result-row">
      <span class="player-tag" style="color:${pc}">${ptxt}</span>
      ${!isPreset?`<button class="undo-btn" onclick="undoMatch('${mid}')">&#8617; undo</button>`:""}
    </div>`;
    // If somehow preset and no player yet, let them still assign
    if(isPreset && !pl){
      action=`<p class="pick-label">Who played?</p>
        <div class="player-btns">
          <button class="pb-p1" onclick="pickPlayer('${mid}','P1')">Ahmad</button>
          <button class="pb-p2" onclick="pickPlayer('${mid}','P2')">Mohammad</button>
        </div>`;
    }

  } else if(waitingPlayer){
    // Winner chosen, pick player
    const wf = dig(mid, w);
    action=`<p class="pick-label">&#9812; ${wf.name} wins — who played?</p>
      <div class="player-btns">
        <button class="pb-p1" onclick="pickPlayer('${mid}','P1')">Ahmad</button>
        <button class="pb-p2" onclick="pickPlayer('${mid}','P2')">Mohammad</button>
      </div>`;

  } else if(bothKnown && !isPreset){
    // Both fighters known, pick winner
    const tn=tf?.name||"Top fighter", bn=bf?.name||"Bot fighter";
    action=`<div class="win-btns">
      <button class="win-btn" onclick="pickWinner('${mid}','top')">${tn} wins</button>
      <button class="win-btn" onclick="pickWinner('${mid}','bot')">${bn} wins</button>
    </div>`;

  } else if(isPreset && !winnerPicked){
    // Preset winner not yet in state — assign player
    action=`<p class="pick-label">&#9812; ${dig(mid, m.preset_winner).name} won — who played?</p>
      <div class="player-btns">
        <button class="pb-p1" onclick="pickPlayer('${mid}','P1')">Ahmad</button>
        <button class="pb-p2" onclick="pickPlayer('${mid}','P2')">Mohammad</button>
      </div>`;
  }

  el.innerHTML = lrow + fline + fbar + action;
}

function updateScoreboard(){
  let p1=0, p2=0;
  Object.values(ST).forEach(r=>{ if(r.player==="P1") p1++; else if(r.player==="P2") p2++; });
  document.getElementById("p1score").textContent=p1;
  document.getElementById("p2score").textContent=p2;
  document.getElementById("p1panel").classList.toggle("lead",p1>p2);
  document.getElementById("p2panel").classList.toggle("lead",p2>p1);
}

function renderAll(){
  Object.keys(BK).forEach(renderCard);
  updateScoreboard();
}
renderAll();
</script>
</body>
</html>"""

with open("tournament.html","w",encoding="utf-8") as f:
    f.write(HTML)
print("\nHTML written to tournament.html")
