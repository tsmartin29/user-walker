#!/usr/bin/env python3
"""walkergate: the small, boring part of an always-on "user walker" agent loop.

A scheduled agent calls this before and after each run so that
  * only one walker runs at a time (a lock that goes stale after N minutes),
  * runs stop once today's spend passes a daily cap,
  * products are walked in rotation.

Standard library only. State lives in one folder (default ~/.config/user-walker).

  walkergate.py start --spent 12.40 [--cap 20] [--five-hour 35]   exit 0 = go, 3 = skip (reason on stdout)
  walkergate.py next                                             prints the product to walk now
  walkergate.py done                                             clears the lock, advances the rotation
  walkergate.py status                                           one line: lock, budget, next product

--spent is the cumulative spend figure your tool reports (any currency, any counter that only goes up).
The first `start` of each local day records it as the baseline; the cap applies to the increase since then.
"""
import argparse
import datetime as _dt
import json
import os
import sys
import time

GO, SKIP = 0, 3


def _dir(args):
    d = os.path.expanduser(args.dir or os.environ.get("USER_WALKER_DIR") or "~/.config/user-walker")
    os.makedirs(d, exist_ok=True)
    return d


def _load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _save(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def _config(d):
    cfg = _load(os.path.join(d, "walker.json"), {})
    products = [p["name"] if isinstance(p, dict) else str(p) for p in cfg.get("products", [])]
    return cfg, products or ["app"]


def lock_age_min(d, now=None):
    """Minutes since the lock was taken, or None when there is no live lock (missing or empty)."""
    try:
        with open(os.path.join(d, "lock")) as f:
            raw = f.read().strip()
    except OSError:
        return None
    if not raw:
        return None
    try:
        return ((now or time.time()) - float(raw)) / 60.0
    except ValueError:
        return None


def cmd_start(args, now=None, today=None):
    d = _dir(args)
    cfg, _ = _config(d)
    now = now or time.time()
    stale = float(args.stale_min if args.stale_min is not None else cfg.get("stale_lock_minutes", 90))
    age = lock_age_min(d, now)
    if age is not None and age < stale:
        print(f"skip: another walker started {age:.0f} min ago")
        return SKIP
    if args.five_hour is not None and args.five_hour >= float(cfg.get("max_five_hour_percent", 90)):
        print(f"skip: 5-hour usage at {args.five_hour:.0f}%")
        return SKIP
    cap = float(args.cap if args.cap is not None else cfg.get("daily_cap", 20))
    today = today or _dt.date.today().isoformat()
    bpath = os.path.join(d, "budget.json")
    b = _load(bpath, {})
    if b.get("date") != today:
        b = {"date": today, "baseline": args.spent}
        _save(bpath, b)
    used = args.spent - float(b.get("baseline", args.spent))
    if used > cap:
        print(f"skip: spent {used:.2f} today, cap {cap:.2f}")
        return SKIP
    with open(os.path.join(d, "lock"), "w") as f:
        f.write(f"{now}\n")
    print(f"go: spent {used:.2f} of {cap:.2f} today; walk {cmd_next(args, quiet=True)}")
    return GO


def cmd_next(args, quiet=False):
    d = _dir(args)
    _, products = _config(d)
    st = _load(os.path.join(d, "state.json"), {})
    nxt = st.get("next") if st.get("next") in products else products[0]
    if not quiet:
        print(nxt)
    return nxt


def cmd_done(args):
    d = _dir(args)
    _, products = _config(d)
    spath = os.path.join(d, "state.json")
    st = _load(spath, {})
    cur = st.get("next") if st.get("next") in products else products[0]
    st["next"] = products[(products.index(cur) + 1) % len(products)]
    st["runs"] = int(st.get("runs", 0)) + 1
    _save(spath, st)
    with open(os.path.join(d, "lock"), "w") as f:   # emptied, not deleted
        f.write("")
    print(f"done: next walker walks {st['next']} (run {st['runs']})")
    return GO


def cmd_status(args):
    d = _dir(args)
    age = lock_age_min(d)
    b = _load(os.path.join(d, "budget.json"), {})
    print(f"lock: {'held ' + format(age, '.0f') + ' min' if age is not None else 'free'} | "
          f"budget day: {b.get('date', '-')} baseline {b.get('baseline', '-')} | next: {cmd_next(args, quiet=True)}")
    return GO


def main(argv=None):
    p = argparse.ArgumentParser(prog="walkergate", description=__doc__.split("\n")[0])
    p.add_argument("--dir", help="state folder (default ~/.config/user-walker or $USER_WALKER_DIR)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start")
    s.add_argument("--spent", type=float, required=True, help="cumulative spend reported by your usage tool")
    s.add_argument("--cap", type=float, help="daily cap (default from walker.json, else 20)")
    s.add_argument("--five-hour", type=float, dest="five_hour", help="current 5-hour usage percent, if you have it")
    s.add_argument("--stale-min", type=float, dest="stale_min", help="minutes after which a lock is stale (default 90)")
    sub.add_parser("next")
    sub.add_parser("done")
    sub.add_parser("status")
    args = p.parse_args(argv)
    fn = {"start": cmd_start, "next": cmd_next, "done": cmd_done, "status": cmd_status}[args.cmd]
    r = fn(args)
    return r if isinstance(r, int) else GO


if __name__ == "__main__":
    sys.exit(main())
