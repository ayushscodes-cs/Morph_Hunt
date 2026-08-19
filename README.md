# MORPH HUNT: The Object Among Us

An original 3D multiplayer asymmetric hide-and-seek prototype built with
**Python 3.11+** and the **Ursina Engine**. Hiders transform into
environment objects (chairs, boxes, plants, crates...) and must complete
objectives while avoiding Hunters, who rely on a limited scanner and
observation — not omniscience — to track them down.

This is an original student-style project. It does not reuse any maps,
art, names, sounds, or code from Prop Hunt, Secret Neighbor, Among Us,
or any other commercial title.

---

## 1. Requirements

- Windows 10/11 (also runs on macOS/Linux for development/testing)
- Python 3.11 or newer
- A graphics driver with OpenGL support (any normal gaming/office PC)

## 2. Installation

```bash
# from the project root (the folder containing main.py)
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

`requirements.txt` installs the Ursina engine (Panda3D is pulled in
automatically as Ursina's dependency).

## 3. Running the game

### Hosting a game (single command — server + client together)

```bash
python main.py
```

Click **HOST GAME** on the main menu, enter your name and a port (or
leave it blank for the default `5555`), then **START HOSTING**. This
launches an authoritative game server in a background thread and
connects your own client to it automatically — you don't need a second
terminal.

### Joining a game

On another PC on the same LAN (or another terminal on the same PC):

```bash
python main.py
```

Click **JOIN GAME**, enter your name and the host's address in the form
`IP:PORT`, for example:

```
127.0.0.1:5555        (same machine)
192.168.1.10:5555     (LAN — use the host's local IP)
```

### Running a dedicated headless server (optional)

If you'd rather run the server without also opening a client window:

```bash
python server/server.py 5555
```

Then have every player (including the host's own machine) **JOIN** that
address instead of hosting.

## 4. Controls

| Key | Action |
|---|---|
| `WASD` | Move |
| Mouse | Look / camera |
| `Shift` | Sprint (Hunters; also affects un-morphed Hiders) |
| `Space` | Jump |
| `1`–`9` | Hider: transform into an object type |
| `E` | Hider: interact with a nearby objective |
| `Q` | Hunter: use scanner |
| Left Click | Hunter: attack |
| `Esc` | Pause / unlock mouse |

## 5. How to play

**Hiders**
1. Find a suitable object and press its number key to transform.
2. Hide naturally — camouflage quality depends on the object type.
3. Complete objectives (switches, terminals, panels, fragments) by
   walking up to them and holding `E`.
4. Watch your **Morph Energy** — moving while disguised drains it;
   standing still lets it regenerate. Hitting zero forces you to
   un-morph.
5. Survive until the timer runs out, or (in **Object Rush** mode)
   finish enough objectives before Hunters find everyone.

**Hunters**
1. Use the scanner (`Q`) for vague clues — it never reveals exact
   positions, only approximate distance/activity hints.
2. Investigate suspicious objects and attack (`Left Click`) — hits
   deal damage over a few charges; eliminating a Hider wins ground for
   your team.
3. Scanner charges regenerate slowly over time, so use them wisely.

## 6. Game modes

- **Classic** — Hunters must eliminate every Hider before time runs out.
- **Object Rush** — Hiders win instantly if they complete 3 objectives.
- **Infection** — eliminated Hiders come back as Hunters instead of
  spectating (architecture is in place; toggle it from the lobby the
  same way as the other modes).

## 7. Levels

Five data-driven levels ship in `maps/`:

1. **House** — the fully hand-laid-out starter map (living room,
   kitchen, bedroom, hallway, storage room, basement, outdoor yard).
2. **Office** — tighter hiding spaces, desks and monitors.
3. **Supermarket** — dense aisles of near-identical crates/boxes/carts
   for tougher camouflage.
4. **Warehouse** — a large map split into four zones.
5. **Factory** — visual hazards and objectives spread across the floor.

All five are built from the same reusable modular room/prop helpers in
`maps/_builder.py`, so adding a sixth level is just a new `maps/*.py`
file returning the same data structure (see any existing map for the
format) plus adding its key to `LEVELS` in `config/settings.py`.

## 8. Project structure

```
morph_hunt/
├── main.py                  entry point
├── requirements.txt
├── README.md
├── client/
│   ├── client.py             Ursina app: scene, input, rendering, screen flow
│   └── network_client.py     TCP client + background receive thread
├── server/
│   ├── server.py              dedicated headless server CLI
│   └── game_server.py         authoritative server: sockets, game loop
├── game/
│   ├── player.py               PlayerState (server-authoritative)
│   ├── hunter.py                scanner + attack resolution
│   ├── hider.py                 hider-only helpers
│   ├── morph_system.py          transform + Morph Energy rules
│   ├── object_prop.py           object "personality" registry
│   ├── objective.py              objective definitions + progress
│   ├── round_manager.py          phase state machine + win conditions
│   ├── level_manager.py          loads maps/*.py by key
│   ├── game_state.py             enums + JSON wire protocol
│   └── stats_db.py               SQLite XP/progression persistence
├── maps/
│   ├── _builder.py               shared modular geometry helpers
│   ├── house.py / office.py / supermarket.py / warehouse.py / factory.py
├── ui/
│   ├── menu.py, lobby.py, hud.py, results.py
├── config/
│   └── settings.py                every balance value in one place
└── assets/
    └── README.md
```

## 9. Balancing the game

Every number that affects gameplay feel — movement speed, Morph Energy
costs/regen, scanner range/cooldown, attack damage, phase timers,
objective counts — lives in `config/settings.py`. Change a value there
and every system (server rules + client prediction) picks it up.

## 10. Networking model (MVP notes)

- Custom length-prefixed JSON protocol (`game/game_state.py`) — no
  `pickle` is used over the wire, since deserializing untrusted pickle
  data is unsafe.
- The server is authoritative for **roles, transformations, round
  state/timers, eliminations, objectives** and broadcasts snapshots
  ~12×/second.
- Player *position* is currently client-reported with only light
  server-side sanity limits (a pragmatic trust model for a LAN
  prototype). Hardening this into full server-side movement simulation
  and anti-cheat validation is a natural next step, not required for a
  trusted-LAN student project.
- Hunters never receive which specific player controls a disguised
  object — only its position/appearance as an object, same as any
  other prop.

## 11. Troubleshooting

- **"Could not connect"** — check the IP/port, that the host's firewall
  allows the chosen port, and that both machines are on the same LAN.
- **Black window / crash on launch** — update your graphics driver;
  Ursina/Panda3D needs OpenGL support.
- **Port already in use** — pick a different port, e.g. `python
  server/server.py 5566`, and join using that port.
- **Players can't see each other move smoothly** — this is an MVP with
  simple position broadcasting rather than full interpolation; minor
  stutter over Wi-Fi is expected.
- Delete `morph_hunt_stats.db` at any time to reset saved XP/progress.

## 12. Known limitations of this MVP

- Position sync is client-authoritative with minimal validation (see
  §10) — fine for a trusted LAN prototype, not for public matchmaking.
- Audio hooks exist as call sites (see inline comments in
  `client/client.py` / `game_server.py` event points) but no audio
  files ship in `assets/`; wire in your own `.ogg`/`.wav` files and
  `Audio(...)` calls from Ursina to activate them.
- Infection mode's role-flip logic is implemented server-side but has
  had the least playtesting of the three modes.
