# user-walker

An always-on QA loop for small teams that build with AI agents: **one agent is always quietly using your software like a real customer.** When it hits an issue, a fixer agent reproduces it in a test and fixes it, both agents answer a short debrief, and a fresh walker starts on the next product.

Built while running ClubPlugins, where one person ships plug-ins, a DJ app and a show-control system with a team of Claude Code agents. Bugs kept surfacing in the places nobody had clicked through since the last change. Unit tests catch what you thought to test; a walker catches what a customer would trip over.

## What's in the box
| File | What it is |
|---|---|
| `PROTOCOL.md` | The loop, the guardrails and the **debrief questionnaire** (9 walker questions, 4 fixer questions) |
| `prompts/walker_task.md` | A prompt template for a scheduled agent run (Claude Code scheduled task, cron + `claude -p`, or similar) |
| `walkergate.py` | The boring part, standard library only: a single-walker lock that goes stale, a **daily spend cap**, product rotation |
| `templates/` | Starting files for the walker log, the debriefs and an issues ledger ("one fix, every product") |
| `examples/walker.json` | Rotation config with per-product walk notes |

## Quick start
```bash
git clone https://github.com/tsmartin29/user-walker && cd user-walker
mkdir -p ~/.config/user-walker && cp examples/walker.json ~/.config/user-walker/   # edit products + cap
python3 walkergate.py status
```
Then schedule `prompts/walker_task.md` (fill in the `{{...}}` paths) to run hourly in your agent runner. Each run:

```bash
python3 walkergate.py start --spent 12.40 --five-hour 35   # exit 0 = go, 3 = skip (prints why)
python3 walkergate.py next                                  # which product to walk
# ... walk, log, fix, debrief ...
python3 walkergate.py done                                  # empty the lock, rotate
```
`--spent` is whatever cumulative spend counter your tool reports. The first run each day records it as the baseline, and the cap applies to the increase since then.

## Why the debrief
Every walker has just used the product end to end, so it's the best-placed reviewer you have. The questionnaire asks it about:
- friction that isn't a bug;
- the top 3 improvements;
- **capabilities one app should borrow from another**;
- duplicated code across apps;
- claims in your docs or ads that the product doesn't back up;
- what would make a new user quit in five minutes;
- a ready-to-ship percentage.

Read the debriefs weekly. Ideas that come up again and again are the ones worth building.

## Guardrails
The loop is only safe to leave running because of the rules in `PROTOCOL.md`:
- scratch data only, and no windows on your screen;
- a reserved port range;
- never publish, push, send or spend;
- never permanently delete;
- security-sensitive code (licensing, protection, installers, signing) is logged for a human, never changed;
- one walker at a time, under a daily cap.

## Tests
```bash
python3 -m unittest discover -s tests
```

MIT. Copyright (c) 2026 Tommy Martin.
