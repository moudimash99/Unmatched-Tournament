import os, hashlib
from pathlib import Path
from flask import Flask, request, session, redirect, send_file, Response

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

ROOT_DIR = Path(__file__).resolve().parent
PW_HASH  = os.environ["PASSWORD_HASH"]
HTML_FILE = os.environ.get("HTML_FILE", "tournament_a.html")

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
  <h1>&#9876; Unmatched Tournament</h1>
  <p>Enter password to access</p>
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
        return send_file(HTML_FILE)
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8742))
    app.run(host="0.0.0.0", port=port)
