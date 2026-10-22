# User Walker protocol

An always-on loop: one agent at a time uses your software the way a real customer would, until it hits an issue. The issue gets fixed with a test, the agent answers a short debrief, and a fresh walker starts on the next product.

## The loop
1. **Gate.** `walkergate.py start` checks that no other walker holds the lock, that today's spend is under the cap, and (optionally) that the 5-hour usage window isn't nearly full.
2. **Walk.** Take `walkergate.py next` and use that product like a first-time customer: install or first run, setup, the main jobs, the edge cases a real person hits, odd inputs. Go slowly and do one thing at a time. Before you start, read the log and debriefs, and pick flows earlier walkers haven't covered.
3. **Stop at the first real issue**: a crash, wrong result, misleading text, broken link, data loss, a step that's too slow, or anything that contradicts your docs, site or ads.
4. **Log it** in `ISSUES_LEDGER.md` and `USER_WALKER_LOG.md`, with exact repro steps and expected vs actual.
5. **Fix it.** One fixer agent writes a failing test that reproduces the issue, fixes it, runs the product's tests, and commits locally. No push and no release; a human decides those.
6. **Debrief** (always, clean runs included): answer the questionnaire below in `WALKER_DEBRIEFS.md`.
7. **Done.** `walkergate.py done` empties the lock and moves the rotation to the next product.

## Debrief questionnaire
**Walker**
1. **Walked:** product, version or branch, flows covered, minutes spent.
2. **Friction that isn't a bug:** slow, confusing, ugly, too many steps, unclear wording.
3. **Top 3 improvements** a customer would notice, each with the pain it solves and the effort (S, M or L).
4. **Cross-app integration:** which capability in this app should another app use, or the other way round, and what it would unlock.
5. **Duplicated or divergent code or behaviour** across apps that should be fixed once and applied everywhere.
6. **Claims check:** anything in the docs, site or ads that the product doesn't do, or does differently.
7. **First 5 minutes:** what would make a first-time user quit?
8. **Ready to ship today:** 0–100%, why, and what would raise it.
9. **Next walker:** what to look at next time.

**Fixer** (only when there was a fix)
1. Root cause, as a pattern rather than just the line.
2. The same pattern elsewhere: grep result and status per product.
3. The test added, and whether it now runs in the normal suite.
4. Any risk the fix introduces.

A human reads the debriefs weekly and turns repeated ideas into proposals. Nothing gets built from a debrief without a human's yes.

## Guardrails (keep these; they are why it's safe to leave running)
- Scratch homes, scratch folders and copies of data only. Never touch the owner's real files, open documents or sessions.
- No windows on the owner's screen: run headless.
- Test servers use a reserved port range that nothing else on the machine uses.
- Never release, publish, deploy, push, send messages or spend money.
- Never permanently delete; move things to the Trash and keep dated backups before overwriting.
- Licensing, copy protection, installers, signing and other security-sensitive code are never changed by the loop. They're logged as OPEN for a human.
- One walker at a time, with a daily cost cap. Cheaper models walk; the stronger model only fixes logic that needs judgment.
