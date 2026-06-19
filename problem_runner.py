import sys
import os
import json
import subprocess
from pathlib import Path

REGISTRY_PATH = Path(__file__).parent / "problems.json"

EXCLUDE_DIRS = {"__pycache__"}
EXCLUDE_FILES = {"problem_runner.py", "problem_manager.py", "problems.json"}


def load_registry():
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return []


def save_registry(reg):
    REGISTRY_PATH.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")


def scan_for_problems(root: Path):
    problems = []
    for p in root.rglob("*.py"):
        if p.name in EXCLUDE_FILES:
            continue
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        rel = p.relative_to(root)
        problems.append({
            "id": str(rel).replace("\\", "/"),
            "path": str(p),
            "title": p.stem,
            "description": ""
        })
    problems.sort(key=lambda x: x["id"])
    return problems


def ensure_registry(root: Path):
    reg = load_registry()
    if not reg:
        reg = scan_for_problems(root)
        save_registry(reg)
    return reg


def print_menu(reg):
    print("\n== python3_mock Problem Launcher ==\n")
    for i, item in enumerate(reg, start=1):
        print(f"{i}. {item.get('title')} — {item.get('id')}")
    print("\nCommands: number to run, r=refresh, s=search, a=add, q=quit")


def run_problem(item, cwd: Path):
    path = item.get("path") or item.get("id")
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    print(f"Running {path} (cwd={cwd})...\n")
    subprocess.run([sys.executable, path], cwd=str(cwd))


def search_registry(reg, term):
    term = term.lower()
    return [r for r in reg if term in r.get("title","").lower() or term in r.get("id","").lower()]


def add_entry_interactive(root: Path, reg):
    path = input("Path to .py file (relative or absolute): ").strip()
    if not path:
        return reg
    p = Path(path)
    if not p.exists():
        p = (root / path)
    if not p.exists():
        print("File does not exist.")
        return reg
    title = input(f"Title [{p.stem}]: ").strip() or p.stem
    try:
        relid = str(p.relative_to(root)).replace("\\", "/")
    except Exception:
        relid = str(p)
    entry = {"id": relid, "path": str(p), "title": title, "description": ""}
    reg.append(entry)
    save_registry(reg)
    print("Added.")
    return reg


def main():
    root = Path(__file__).parent
    reg = ensure_registry(root)
    while True:
        print_menu(reg)
        cmd = input("> ").strip()
        if cmd == "q":
            break
        if cmd == "r":
            reg = scan_for_problems(root)
            save_registry(reg)
            print("Refreshed registry from workspace scan.")
            continue
        if cmd == "s":
            term = input("Search: ").strip()
            results = search_registry(reg, term)
            for i, item in enumerate(results, start=1):
                print(f"{i}. {item.get('title')} — {item.get('id')}")
            continue
        if cmd == "a":
            reg = add_entry_interactive(root, reg)
            continue
        try:
            idx = int(cmd) - 1
            if 0 <= idx < len(reg):
                run_problem(reg[idx], root)
            else:
                print("Invalid selection.")
        except ValueError:
            print("Unknown command.")


if __name__ == "__main__":
    main()
