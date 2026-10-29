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
        return {"thing": data.get("thing"), "streak": int(data.get("streak", 0)),
                "done": done if isinstance(done, list) else []}
    except (OSError, ValueError, AttributeError):
        return {"thing": None, "streak": 0, "done": []}


def save(state):
    path = data_file()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state), encoding="utf-8")
    os.replace(tmp, path)  # atomic: a crash never leaves a half-written file


def show(state):
    if not state["thing"]:
        print(QUESTION)
        print('Set it:  one set "..."')
        return
    line = f"  ONE thing: {state['thing']}  "
    print("+" + "-" * len(line) + "+")
    print("|" + line + "|")
    print("+" + "-" * len(line) + "+")
    print(f"  streak: {state['streak']}   start:  one go")


def beep():
    try:
        import winsound
        winsound.Beep(880, 600)
    except (ImportError, RuntimeError):
        print("\a", end="")


def go(minutes):
    end = time.monotonic() + minutes * 60
    try:
        while (left := end - time.monotonic()) > 0:
            m, s = divmod(int(left + 0.999), 60)
            print(f"\r  focus  {m:02d}:{s:02d} ", end="", flush=True)
            time.sleep(min(1, left))
    except KeyboardInterrupt:
        print("\r  stopped.          ")
        return 0
    print("\r  DONE. Time's up.  ")
    beep()
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="one", description="Focus on ONE thing. Run 'one' alone to see it.")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("set", help="set your ONE thing")
    s.add_argument("text", nargs="+")
    g = sub.add_parser("go", help="start a focus timer: one go [minutes], default 25")
    g.add_argument("minutes", nargs="?", type=float, default=25)
    sub.add_parser("done", help="finish your ONE thing")
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
    elif args.cmd == "go":
        if args.minutes <= 0:
            print("Minutes must be more than 0.", file=sys.stderr)
            return 1
        return go(args.minutes)
    elif args.cmd == "done":
        if not state["thing"]:
            print('Nothing set. Run:  one set "..."', file=sys.stderr)
            return 1
        print(f"Done: {state['thing']}")
        state["done"].append({"thing": state["thing"],
                              "at": datetime.now().strftime("%Y-%m-%d %H:%M")})
        state["thing"] = None
        state["streak"] += 1
        save(state)
        print(f"Streak: {state['streak']}\n\nNext: {QUESTION}")
    elif args.cmd == "log":
        print(f"Streak: {state['streak']}")
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
