"""Spearhead League — Age of Sigmar Spearhead game tracker, ladder and match-up suggester.

Flask + SQLite. Run:  python app.py   (or via gunicorn / the systemd unit in README.md)
Env vars:
  ADMIN_KEY      key for the Admin page (settings, rename/delete players, fix/delete games)
  SPEARHEAD_DB   path to the SQLite file (default: spearhead.db next to this file)
  PORT           port to listen on (default 8095)
"""
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import threading
import time
import uuid

from flask import Flask, abort, g, jsonify, request, send_from_directory

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("SPEARHEAD_DB", os.path.join(BASE, "spearhead.db"))
ADMIN_KEY = os.environ.get("ADMIN_KEY", "")
DEFAULT_SETTINGS = {"club": "The Dirty d6 Dozen", "win": 3, "draw": 1, "loss": 0,
                    "play": 1, "upset": 1, "rounds": 4, "extra_warbands": [],
                    "idle_days": 14, "idle_top": 3, "idle_mid": 2, "idle_low": 1}
INT_SETTINGS = ("win", "draw", "loss", "play", "upset", "rounds", "idle_days", "idle_top", "idle_mid", "idle_low")
DOWNLOADS = os.path.join(BASE, "static", "downloads")
APK_NAME = "spearhead-league.apk"

app = Flask(__name__, static_folder="static", static_url_path="/static")
WRITE_LOCK = threading.Lock()


@app.after_request
def cors(resp):
    # The Android app runs from its own origin, so the API must allow cross-origin calls.
    if request.path.startswith("/api/"):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Admin-Key, X-Player-Token"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
    return resp


@app.route("/api/<path:_any>", methods=["OPTIONS"])
def preflight(_any):
    return ("", 204)


# ---------------------------------------------------------------- database
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, timeout=10)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    d = g.pop("db", None)
    if d is not None:
        d.close()


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
    PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS players(
        id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE COLLATE NOCASE,
        faction TEXT DEFAULT '', created REAL);
    CREATE TABLE IF NOT EXISTS games(
        id TEXT PRIMARY KEY, status TEXT NOT NULL, mode TEXT NOT NULL,
        created REAL, updated REAL, finished REAL, data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, pid TEXT NOT NULL, created REAL);
    """)
    cols = {r[1] for r in con.execute("PRAGMA table_info(players)")}
    if "pin_hash" not in cols:
        con.execute("ALTER TABLE players ADD COLUMN pin_hash TEXT DEFAULT ''")
    if "warband" not in cols:
        con.execute("ALTER TABLE players ADD COLUMN warband TEXT DEFAULT ''")
    con.execute("INSERT OR IGNORE INTO meta VALUES('rev','1')")
    con.execute("INSERT OR IGNORE INTO meta VALUES('settings',?)", (json.dumps(DEFAULT_SETTINGS),))
    con.commit()
    con.close()


def get_meta(key):
    r = db().execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return r["value"] if r else None


def bump():
    db().execute("UPDATE meta SET value=CAST(value AS INTEGER)+1 WHERE key='rev'")


def settings():
    s = dict(DEFAULT_SETTINGS)
    s.update({k: v for k, v in json.loads(get_meta("settings") or "{}").items() if k in DEFAULT_SETTINGS})
    return s


def game_row(gid):
    r = db().execute("SELECT * FROM games WHERE id=?", (gid,)).fetchone()
    if not r:
        abort(404, "Game not found")
    return r


def game_out(r):
    d = json.loads(r["data"])
    d.update(id=r["id"], status=r["status"], mode=r["mode"], created=r["created"],
             updated=r["updated"], finished=r["finished"])
    return d


def state():
    d = db()
    return {
        "rev": int(get_meta("rev")),
        "settings": settings(),
        "players": [{"id": r["id"], "name": r["name"], "faction": r["faction"], "warband": r["warband"] or "",
                     "has_pin": bool(r["pin_hash"])}
                    for r in d.execute("SELECT * FROM players ORDER BY name COLLATE NOCASE")],
        "games": [game_out(r) for r in d.execute(
            "SELECT * FROM games WHERE status IN ('live','done') ORDER BY created")],
        "server_time": time.time(),
    }


def commit_and_state(**extra):
    bump()
    db().commit()
    out = state()
    out.update(extra)
    return jsonify(out)


def body():
    return request.get_json(silent=True) or {}


def is_admin():
    key = request.headers.get("X-Admin-Key") or request.args.get("key") or ""
    return bool(ADMIN_KEY) and key == ADMIN_KEY


def need_admin():
    if not is_admin():
        abort(403, "Admin key required")


# ---------------------------------------------------------------- player PINs
FAILS = {}  # pid -> [count, locked_until]


def hash_pin(pin):
    salt = secrets.token_hex(8)
    dk = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${dk}"


def check_pin(pin, stored):
    try:
        salt, dk = stored.split("$", 1)
    except ValueError:
        return False
    return hmac.compare_digest(hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), 100_000).hex(), dk)


def valid_pin(pin):
    pin = str(pin or "").strip()
    if not (pin.isdigit() and 4 <= len(pin) <= 6):
        abort(400, "PIN must be 4 to 6 digits")
    return pin


def new_session(pid):
    token = secrets.token_urlsafe(24)
    db().execute("INSERT INTO sessions VALUES(?,?,?)", (token, pid, time.time()))
    return token


def current_player():
    token = request.headers.get("X-Player-Token") or ""
    if not token:
        return None
    r = db().execute("SELECT pid FROM sessions WHERE token=?", (token,)).fetchone()
    return r["pid"] if r else None


def need_player():
    pid = current_player()
    if not pid:
        abort(401, "Please log in with your PIN")
    return pid


def need_in_game(d):
    if is_admin():
        return
    pid = need_player()
    if not any(pid in t for t in d["teams"]):
        abort(403, "Only the players in this game can change it")


@app.errorhandler(401)
@app.errorhandler(429)
@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(409)
def err(e):
    return jsonify(error=getattr(e, "description", str(e))), e.code


# ---------------------------------------------------------------- pages
@app.route("/")
def index():
    resp = send_from_directory(app.static_folder, "index.html")
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@app.route("/config.js")
def web_config():
    # The Android app ships its own config.js (server address + build number); the web version needs none.
    resp = app.response_class("window.SPEARHEAD_SERVER='';window.SPEARHEAD_VERSION=0;", mimetype="application/javascript")
    resp.headers["Cache-Control"] = "no-cache"
    return resp


# ---------------------------------------------------------------- state
@app.get("/api/state")
def api_state():
    known = request.args.get("rev", type=int)
    rev = int(get_meta("rev"))
    if known is not None and known == rev:
        return jsonify(rev=rev, same=True)
    return jsonify(state())


# ---------------------------------------------------------------- players
@app.post("/api/players")
def add_player():
    b = body()
    name = (b.get("name") or "").strip()[:40]
    if not name:
        abort(400, "Name required")
    pin = valid_pin(b.get("pin"))
    with WRITE_LOCK:
        if db().execute("SELECT 1 FROM players WHERE name=?", (name,)).fetchone():
            abort(409, "That name is already taken — pick it from the list instead")
        pid = uuid.uuid4().hex[:10]
        db().execute("INSERT INTO players(id,name,faction,warband,created,pin_hash) VALUES(?,?,?,?,?,?)",
                     (pid, name, (b.get("faction") or "")[:60], (b.get("warband") or "")[:80], time.time(), hash_pin(pin)))
        token = new_session(pid)
        return commit_and_state(new_id=pid, token=token)


@app.post("/api/login")
def login():
    b = body()
    pid = b.get("pid") or ""
    pin = valid_pin(b.get("pin"))
    with WRITE_LOCK:
        r = db().execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone()
        if not r:
            abort(404, "Player not found")
        cnt, until = FAILS.get(pid, [0, 0])
        if until > time.time():
            abort(429, f"Too many wrong PINs — try again in {int(until - time.time()) // 60 + 1} min")
        if not r["pin_hash"]:
            # player created before PINs existed: the first PIN entered becomes theirs
            db().execute("UPDATE players SET pin_hash=? WHERE id=?", (hash_pin(pin), pid))
        elif not check_pin(pin, r["pin_hash"]):
            cnt += 1
            FAILS[pid] = [0, time.time() + 300] if cnt >= 5 else [cnt, 0]
            abort(403, "Wrong PIN" + (" — locked for 5 minutes" if cnt >= 5 else ""))
        FAILS.pop(pid, None)
        token = new_session(pid)
        return commit_and_state(token=token, new_id=pid)


@app.post("/api/logout")
def logout():
    token = request.headers.get("X-Player-Token") or ""
    with WRITE_LOCK:
        db().execute("DELETE FROM sessions WHERE token=?", (token,))
        db().commit()
    return jsonify(ok=True)


@app.post("/api/players/<pid>/reset-pin")
def reset_pin(pid):
    need_admin()
    pin = valid_pin(body().get("pin"))
    with WRITE_LOCK:
        if not db().execute("SELECT 1 FROM players WHERE id=?", (pid,)).fetchone():
            abort(404, "Player not found")
        db().execute("UPDATE players SET pin_hash=? WHERE id=?", (hash_pin(pin), pid))
        db().execute("DELETE FROM sessions WHERE pid=?", (pid,))  # log them out everywhere
        return commit_and_state()


@app.patch("/api/players/<pid>")
def edit_player(pid):
    b = body()
    with WRITE_LOCK:
        if not db().execute("SELECT 1 FROM players WHERE id=?", (pid,)).fetchone():
            abort(404, "Player not found")
        if "faction" in b or "warband" in b:
            if not is_admin() and need_player() != pid:
                abort(403, "You can only change your own warband")
            if "faction" in b:
                db().execute("UPDATE players SET faction=? WHERE id=?", ((b["faction"] or "")[:60], pid))
            if "warband" in b:
                db().execute("UPDATE players SET warband=? WHERE id=?", ((b["warband"] or "")[:80], pid))
        if "name" in b:
            need_admin()
            name = (b["name"] or "").strip()[:40]
            if not name:
                abort(400, "Name required")
            try:
                db().execute("UPDATE players SET name=? WHERE id=?", (name, pid))
            except sqlite3.IntegrityError:
                abort(409, "Name already taken")
        return commit_and_state()


@app.delete("/api/players/<pid>")
def del_player(pid):
    if not is_admin() and need_player() != pid:
        abort(403, "You can only delete your own account")
    with WRITE_LOCK:
        for r in db().execute("SELECT data FROM games"):
            d = json.loads(r["data"])
            if any(pid in t for t in d["teams"]):
                abort(409, "This account has games on the ladder, so it can't be deleted. Ask the organiser to merge it into your other account.")
        db().execute("DELETE FROM players WHERE id=?", (pid,))
        db().execute("DELETE FROM sessions WHERE pid=?", (pid,))
        return commit_and_state()


@app.post("/api/players/<src>/merge")
def merge_player(src):
    """Admin: move every game from one account into another, then remove the first account."""
    need_admin()
    dst = body().get("into") or ""
    if not dst or dst == src:
        abort(400, "Pick a different account to merge into")
    with WRITE_LOCK:
        ids = {r["id"] for r in db().execute("SELECT id FROM players WHERE id IN (?,?)", (src, dst))}
        if ids != {src, dst}:
            abort(404, "Player not found")
        rows = db().execute("SELECT id, data FROM games").fetchall()
        for r in rows:
            d = json.loads(r["data"])
            flat = [p for t in d["teams"] for p in t]
            if src in flat and dst in flat:
                abort(409, "These two accounts played in the same game, so they can't be merged")
        for r in rows:
            d = json.loads(r["data"])
            if not any(src in t for t in d["teams"]):
                continue
            d["teams"] = [[dst if p == src else p for p in t] for t in d["teams"]]
            for k in ("factions", "warbands", "cp"):
                if k in d and src in d[k]:
                    d[k][dst] = d[k].pop(src)
            db().execute("UPDATE games SET data=? WHERE id=?", (json.dumps(d), r["id"]))
        db().execute("DELETE FROM players WHERE id=?", (src,))
        db().execute("DELETE FROM sessions WHERE pid=?", (src,))
        return commit_and_state()


# ---------------------------------------------------------------- games
def valid_teams(mode, teams):
    size = 1 if mode == "1v1" else 2
    if not (isinstance(teams, list) and len(teams) == 2 and all(isinstance(t, list) and len(t) == size for t in teams)):
        abort(400, "Pick all the players for both sides")
    flat = [p for t in teams for p in t]
    if len(set(flat)) != len(flat) or not all(flat):
        abort(400, "Each player can only be on the field once")
    known = {r["id"] for r in db().execute("SELECT id FROM players")}
    if not set(flat) <= known:
        abort(400, "Unknown player")
    return flat


@app.post("/api/games")
def new_game():
    b = body()
    mode = b.get("mode") if b.get("mode") in ("1v1", "2v2") else "1v1"
    with WRITE_LOCK:
        teams = b.get("teams")
        flat = valid_teams(mode, teams)
        if not is_admin() and need_player() not in flat:
            abort(403, "You can only start games you're playing in")
        rounds = int(settings()["rounds"])
        factions = {p: str((b.get("factions") or {}).get(p) or "")[:60] for p in flat}
        warbands = {p: str((b.get("warbands") or {}).get(p) or "")[:80] for p in flat}
        now = time.time()
        data = {"teams": teams, "factions": factions, "warbands": warbands, "round": 1,
                "setup": {"done": b.get("final") is not None},
                "vp": [[0, 0] for _ in range(rounds)], "cp": {p: 0 for p in flat},
                "ladder": bool(b.get("ladder", True)), "by": b.get("by") or "", "note": ""}
        status = "live"
        finished = None
        final = b.get("final")
        if final is not None:  # logging an already-played game
            try:
                a, c = int(final[0]), int(final[1])
            except (TypeError, ValueError, IndexError):
                abort(400, "Enter both scores")
            data["vp"] = [[a, c]] + [[0, 0] for _ in range(rounds - 1)]
            data["round"] = rounds
            data["final_only"] = True
            status, finished = "done", now
        gid = uuid.uuid4().hex[:10]
        db().execute("INSERT INTO games VALUES(?,?,?,?,?,?,?)",
                     (gid, status, mode, now, now, finished, json.dumps(data)))
        return commit_and_state(new_id=gid)


def mutate_live(gid, fn):
    with WRITE_LOCK:
        r = game_row(gid)
        if r["status"] != "live":
            abort(409, "This game has already finished")
        d = json.loads(r["data"])
        need_in_game(d)
        fn(d)
        db().execute("UPDATE games SET data=?, updated=? WHERE id=?", (json.dumps(d), time.time(), gid))
        return commit_and_state()


@app.post("/api/games/<gid>/vp")
def game_vp(gid):
    b = body()

    def f(d):
        side, rnd, delta = int(b.get("side", 0)), int(b.get("round", 1)), int(b.get("delta", 0))
        if side not in (0, 1) or not 1 <= rnd <= len(d["vp"]) or abs(delta) > 50:
            abort(400, "Bad score change")
        d["vp"][rnd - 1][side] = max(0, d["vp"][rnd - 1][side] + delta)
    return mutate_live(gid, f)


@app.post("/api/games/<gid>/cp")
def game_cp(gid):
    b = body()

    def f(d):
        pid, delta = b.get("pid"), int(b.get("delta", 0))
        if pid not in d["cp"] or abs(delta) > 10:
            abort(400, "Bad CP change")
        d["cp"][pid] = max(0, d["cp"][pid] + delta)
    return mutate_live(gid, f)


@app.post("/api/games/<gid>/round")
def game_round(gid):
    b = body()

    def f(d):
        rnd = int(b.get("round", 1))
        if not 1 <= rnd <= len(d["vp"]):
            abort(400, "Bad round")
        d["round"] = rnd
    return mutate_live(gid, f)


SETUP_KEYS = {"rolloff": (0, 1), "attacker": (0, 1), "first_turn": (0, 1)}


@app.post("/api/games/<gid>/setup")
def game_setup(gid):
    """Pre-battle sequence: roll-off winner, attacker, first turn, realm, checklist, per-round first turn."""
    b = body()

    def f(d):
        st = d.setdefault("setup", {})
        for k, allowed in SETUP_KEYS.items():
            if k in b:
                if b[k] is not None and b[k] not in allowed:
                    abort(400, "Bad value for " + k)
                st[k] = b[k]
        if "realm" in b:
            st["realm"] = str(b["realm"] or "")[:60]
        if "step" in b:
            st["step"] = max(0, min(20, int(b["step"])))
        if "done" in b:
            st["done"] = bool(b["done"])
        if "round_first" in b:  # {"round": n, "side": 0|1|null}
            rf = b["round_first"] or {}
            rnd, side = int(rf.get("round", 0)), rf.get("side")
            if not 1 <= rnd <= len(d["vp"]) or side not in (0, 1, None):
                abort(400, "Bad first-turn value")
            st.setdefault("firsts", {})[str(rnd)] = side
    return mutate_live(gid, f)


@app.post("/api/games/<gid>/finish")
def game_finish(gid):
    with WRITE_LOCK:
        r = game_row(gid)
        if r["status"] != "live":
            abort(409, "Already finished")
        need_in_game(json.loads(r["data"]))
        now = time.time()
        db().execute("UPDATE games SET status='done', finished=?, updated=? WHERE id=?", (now, now, gid))
        return commit_and_state()


@app.post("/api/games/<gid>/abandon")
def game_abandon(gid):
    with WRITE_LOCK:
        r = game_row(gid)
        if r["status"] != "live":
            abort(409, "Only live games can be abandoned")
        need_in_game(json.loads(r["data"]))
        db().execute("DELETE FROM games WHERE id=?", (gid,))
        return commit_and_state()


@app.post("/api/games/<gid>/fix")
def game_fix(gid):
    """Admin: correct a finished game's per-round VP and/or ladder flag."""
    need_admin()
    b = body()
    with WRITE_LOCK:
        r = game_row(gid)
        d = json.loads(r["data"])
        if "vp" in b:
            vp = b["vp"]
            if not (isinstance(vp, list) and all(isinstance(x, list) and len(x) == 2 for x in vp)):
                abort(400, "Bad VP table")
            d["vp"] = [[max(0, int(x[0])), max(0, int(x[1]))] for x in vp]
        if "ladder" in b:
            d["ladder"] = bool(b["ladder"])
        db().execute("UPDATE games SET data=?, updated=? WHERE id=?", (json.dumps(d), time.time(), gid))
        return commit_and_state()


@app.delete("/api/games/<gid>")
def game_delete(gid):
    need_admin()
    with WRITE_LOCK:
        game_row(gid)
        db().execute("DELETE FROM games WHERE id=?", (gid,))
        return commit_and_state()


# ---------------------------------------------------------------- admin
@app.get("/api/admin/check")
def admin_check():
    return jsonify(ok=is_admin(), configured=bool(ADMIN_KEY))


@app.post("/api/settings")
def save_settings():
    need_admin()
    b = body()
    s = settings()
    for k in INT_SETTINGS:
        if k in b:
            try:
                s[k] = int(b[k])
            except (TypeError, ValueError):
                abort(400, f"{k} must be a whole number")
    s["rounds"] = max(1, min(8, s["rounds"]))
    if "club" in b:
        s["club"] = str(b["club"])[:60]
    if "extra_warbands" in b:
        ew = b["extra_warbands"]
        if not isinstance(ew, list):
            abort(400, "Bad warband list")
        s["extra_warbands"] = [{"faction": str(x.get("faction", ""))[:60], "name": str(x.get("name", ""))[:80]}
                               for x in ew if isinstance(x, dict) and x.get("name")][:100]
    with WRITE_LOCK:
        db().execute("UPDATE meta SET value=? WHERE key='settings'", (json.dumps(s),))
        return commit_and_state()


@app.get("/api/app-info")
def app_info():
    """Tells the web page / app whether an Android download is on this Pi, and its build number."""
    apk = os.path.join(DOWNLOADS, APK_NAME)
    version = 0
    try:
        with open(os.path.join(DOWNLOADS, "version.txt")) as f:
            version = int(f.read().strip() or 0)
    except (OSError, ValueError):
        pass
    return jsonify(apk=os.path.exists(apk), version=version, url="/download")


@app.get("/download")
def download_apk():
    if not os.path.exists(os.path.join(DOWNLOADS, APK_NAME)):
        abort(404, "The Android app hasn't been put on the server yet")
    return send_from_directory(DOWNLOADS, APK_NAME, as_attachment=True,
                               mimetype="application/vnd.android.package-archive")


@app.get("/api/export")
def export():
    need_admin()
    resp = jsonify(state())
    resp.headers["Content-Disposition"] = f"attachment; filename=spearhead-backup-{time.strftime('%Y%m%d')}.json"
    return resp


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8095)), threaded=True)
