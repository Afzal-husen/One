"""one: focus on ONE thing at a time (Gary Keller's The ONE Thing)."""
import argparse
import io
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

QUESTION = ("What's the ONE thing I can do such that by doing it "
            "everything else will be easier or unnecessary?")


def data_file():
    return Path(os.environ.get("ONE_FILE", Path.home() / ".one.json"))


def load():
    try:
        data = json.loads(data_file().read_text(encoding="utf-8"))
        done = data.get("done", [])
        started = data.get("started")
        return {"thing": data.get("thing"), "streak": int(data.get("streak", 0)),
                "done": done if isinstance(done, list) else [],
                "started": float(started) if started is not None else None,
                "best": float(data.get("best", 0))}
    except (OSError, ValueError, TypeError, AttributeError):
        return {"thing": None, "streak": 0, "done": [], "started": None, "best": 0.0}


def save(state):
    path = data_file()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state), encoding="utf-8")
    os.replace(tmp, path)  # atomic: a crash never leaves a half-written file


def hms(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}"


def show(state):
    if not state["thing"]:
        print(QUESTION)
        print('Set it:  one set "..."')
        return
    line = f"  ONE thing: {state['thing']}  "
    print("+" + "-" * len(line) + "+")
    print("|" + line + "|")
    print("+" + "-" * len(line) + "+")
    if state["started"] is not None:
        print(f"  running: {hms(time.time() - state['started'])}   "
              f"record: {hms(state['best'])}   stop:  one stop")
    else:
        print(f"  streak: {state['streak']}   record: {hms(state['best'])}   start:  one start")


def stop(state):
    """Stop the stopwatch, update the record. Caller saves."""
    took = time.time() - state["started"]
    state["started"] = None
    print(f"Focused: {hms(took)}")
    if took > state["best"]:
        print(f"NEW RECORD! (was {hms(state['best'])})")
        state["best"] = took
    else:
        print(f"Record: {hms(state['best'])}  ({hms(state['best'] - took)} to beat it)")


def main(argv=None):
    p = argparse.ArgumentParser(prog="one", description="Focus on ONE thing. Run 'one' alone to see it.")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("set", help="set your ONE thing")
    s.add_argument("text", nargs="+")
    sub.add_parser("start", help="start the stopwatch")
    sub.add_parser("stop", help="stop the stopwatch, see if you beat your record")
    sub.add_parser("done", help="finish your ONE thing (also stops the stopwatch)")
    sub.add_parser("log", help="list everything you've finished")
    sub.add_parser("help", help="show this help")
    args = p.parse_args(argv)
    if args.cmd == "help":
        p.print_help()
        return 0

    state = load()
    if args.cmd == "set":
        text = " ".join(args.text).strip()
        if not text:
            print("Empty. What's the ONE thing?", file=sys.stderr)
            return 1
        state["thing"] = text
        save(state)
        show(state)
    elif args.cmd == "start":
        if state["started"] is not None:
            print(f"Already running: {hms(time.time() - state['started'])}", file=sys.stderr)
            return 1
        state["started"] = time.time()
        save(state)
        print(f"Started. Record to beat: {hms(state['best'])}")
    elif args.cmd == "stop":
        if state["started"] is None:
            print("Not running. Start with:  one start", file=sys.stderr)
            return 1
        stop(state)
        save(state)
    elif args.cmd == "done":
        if not state["thing"]:
            print('Nothing set. Run:  one set "..."', file=sys.stderr)
            return 1
        if state["started"] is not None:
            stop(state)
        print(f"Done: {state['thing']}")
        state["done"].append({"thing": state["thing"],
                              "at": datetime.now().strftime("%Y-%m-%d %H:%M")})
        state["thing"] = None
        state["streak"] += 1
        save(state)
        print(f"Streak: {state['streak']}\n\nNext: {QUESTION}")
    elif args.cmd == "log":
        print(f"Streak: {state['streak']}   Record: {hms(state['best'])}")
        if not state["done"]:
            print("Nothing logged yet. Finish one with:  one done")
        for i, d in enumerate(state["done"], 1):
            print(f"  {i:>3}. {d.get('at', '?')}  {d.get('thing', '?')}")
    else:
        show(state)
    return 0


if __name__ == "__main__":
    # Git Bash gives Python a cp1252 stdout; force UTF-8 so emoji/accents don't crash
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    sys.exit(main())
