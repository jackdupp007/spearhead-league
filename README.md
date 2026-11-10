# Spearhead League

An Android app plus a Raspberry Pi server for running an Age of Sigmar **Spearhead** club ladder. Players install the app, start games against each other, and score them live on their own phones. Every phone (and the web page) sees the score update within about 2 seconds.

```
server/   Flask + SQLite — runs on the Pi, holds the ladder, serves the app download
app/      Android app (Capacitor) — uses the same screens as server/static/index.html
.github/  GitHub Actions workflow that builds the signed Android app (.apk)
```

## How it plays

- **First open:** the app asks for the club server address (unless one is built in, see below). Then the person taps their name, adds themselves as a new player, or continues as a viewer.
- **Starts on the Ladder:** one ladder for both 1v1 and 2v2. Tap **Play** next to anyone, or use **Suggested for you**.
- **Live game:** both players tap VP +/− for each battle round and track their own command points. Scores sync between phones, and anyone can watch from the **Live** tab. Only the players in the game (or the admin) can change the score.
- **2v2:** each team scores one combined VP total per round. Every player on the winning team gets the win points.
- **Match-ups:** tick who's here for suggested 1v1 pairings or balanced 2v2 teams. These are only suggestions.
- **Already played?** On the New game screen, tick "Already played — just enter the final score".

### Points (all changeable in Admin)

| | Points |
|---|---|
| Win | 3 |
| Draw | 1 |
| Loss | 0 |
| Played a game | +1 |
| **Upset** — win against a side ranked above you | +1 |

- Upsets are judged on ladder positions just before the game. In 2v2 it uses each team's average position. Players with no games yet count as ranked below everyone, so a newcomer beating a ranked player earns the upset bonus.
- Ladder order is points, then VP difference, then wins.
- Each finished game shows exactly what each player earned, e.g. "Win +3 · Played +1 · Upset +1".
- Changing the points in Admin recalculates the whole ladder from every game.

---

## Part 1 — Set up the Pi server

```bash
scp -r server pi@<pi-ip>:/home/pi/spearhead       # from your PC
ssh pi@<pi-ip>
cd /home/pi/spearhead
python3 -m venv venv && venv/bin/pip install -r requirements.txt
ADMIN_KEY=test venv/bin/python app.py              # quick test → http://<pi-ip>:8095
```

Run it as a service (starts on boot):

```bash
nano spearhead.service            # set ADMIN_KEY to your own secret (and User/paths if not 'pi')
sudo cp spearhead.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now spearhead
journalctl -u spearhead -f        # logs
```

**Make it reachable from outside:** the hostname is **dirtyspearhead.ddns.net** (No-IP). Give the Pi a fixed IP (DHCP reservation), and forward an external port on the router to the Pi's port **8095**. Ports 5000–5250 are used by Traccar on this Pi, so Spearhead uses 8095. The club server address is then `http://dirtyspearhead.ddns.net:8095`.

**Backups:** copy `spearhead.db` (stop the service first), or use Admin → Download backup from a computer.

## Part 2 — Build the Android app (GitHub does it for you)

1. Push this whole folder to a GitHub repo, e.g. `jackdupp007/spearhead-league`.
2. In the repo go to **Settings → Secrets and variables → Actions** and add these four **secrets**. The values are in `SIGNING-KEY-KEEP-SAFE.txt`:
   - `KEYSTORE_BASE64`
   - `KEYSTORE_PASSWORD`
   - `KEY_ALIAS`
   - `KEY_PASSWORD`
3. The club server `http://dirtyspearhead.ddns.net:8095` is already built into the app, so players never type an address. If it ever changes, add a repo **Variable** `SERVER_URL` with the new address and rebuild.
4. Go to **Actions → Build Android app → Run workflow**. It also runs on every push to `main`. After about 5 minutes the **Releases** page has:
   - `spearhead-league.apk`: the app itself
   - `spearhead-pi-download.zip`: the app ready to put on the Pi

**Keep the signing key safe** (`spearhead-release.keystore` plus its passwords). Every update must be signed with the same key, or phones will refuse to update the app.

## Part 3 — Get the app onto phones

1. Unzip `spearhead-pi-download.zip` into `server/static/` on the Pi. That creates `static/downloads/spearhead-league.apk` and `version.txt`. No restart needed.
2. Players open `http://dirtyspearhead.ddns.net:8095` in their phone browser and tap **Download the app**. Or share the link `http://dirtyspearhead.ddns.net:8095/download` in the club chat.
3. Open the downloaded file. Android will ask to allow installs from the browser the first time.

**Updating:** when you build a new version and put the new zip on the Pi, everyone's app shows **"A new version is available — Update"**.

The web page still works in any browser at the same address. It's handy for watching the ladder on a TV or doing admin from a PC.

## Admin

Tap **Admin** at the bottom of any screen and enter your `ADMIN_KEY` to:

- change points, battle rounds and the club name
- rename or delete players
- fix or delete a result (open the result from History)

## Notes

- Players don't have passwords. It's a club app, so anyone can tap any name. Score changes are limited to the players in the game, and fixes or deletions need the admin key.
- The connection to the Pi is plain http unless you add HTTPS (e.g. Caddy in front with ports 80/443 forwarded). If you do, change the server address to `https://…`.
- Keep gunicorn at `-w 1` (one worker with threads) so score taps from both phones never clash.
