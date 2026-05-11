import os, hashlib, json
from pathlib import Path
from flask import Flask, request, session, redirect, send_file, Response

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

ROOT_DIR = Path(__file__).resolve().parent.parent
PW_HASH  = os.environ["PASSWORD_HASH"]
HTML_FILE = Path(os.environ.get("HTML_FILE", "generated/tournament_a.html"))
if not HTML_FILE.is_absolute():
  HTML_FILE = ROOT_DIR / HTML_FILE

STATE_FILE = ROOT_DIR / "data" / "state.json"
WIN_PCT_FILE = ROOT_DIR / "data" / "merged_win_pct.json"
try:
    WIN_PCT = json.loads(WIN_PCT_FILE.read_text(encoding="utf-8"))
except Exception:
    WIN_PCT = {}

def check(pw):
    return hashlib.sha256(pw.encode()).hexdigest() == PW_HASH

LOGIN = """<!DOCTYPE html>
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
  <h1>&#9876; Unmatched Tournament </h1>
  <p>Enter password to access the tournament</p>
  <form method="POST">
    <input type="password" name="password" placeholder="Password" autofocus>
    <button type="submit">Enter</button>
    {error}
  </form>
</div>
</body></html>"""

@app.route("/", methods=["GET", "POST"])
def index():
    if session.get("auth"):
        return send_file(str(HTML_FILE))
    if request.method == "POST":
        if check(request.form.get("password", "")):
            session["auth"] = True
            return redirect("/")
        return LOGIN.replace("{error}", '<p class="err">Incorrect password</p>'), 401
    return LOGIN.replace("{error}", "")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/api/state", methods=["GET"])
def get_state():
    if not session.get("auth"):
        return "", 401
    if STATE_FILE.exists():
        return Response(STATE_FILE.read_text(encoding="utf-8"), content_type="application/json")
    return Response("{}", content_type="application/json")

@app.route("/api/state", methods=["POST"])
def set_state():
    if not session.get("auth"):
        return "", 401
    data = request.get_json(force=True, silent=True)
    if data is None:
        return "", 400
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data), encoding="utf-8")
    return "", 204

@app.route("/api/win-pct", methods=["GET"])
def get_win_pct():
    if not session.get("auth"):
        return "", 401
    a = request.args.get("a", "")
    b = request.args.get("b", "")
    if not a or not b:
        return "", 400
    return {
        "wp": WIN_PCT.get(a, {}).get(b),
        "wp_b": WIN_PCT.get(b, {}).get(a),
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8742))
    app.run(host="0.0.0.0", port=port)
