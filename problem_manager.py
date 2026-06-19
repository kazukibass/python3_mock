"""
problem_manager.py  ─  問題集セット & 問題の管理ツール

使い方:
  セット管理
    python problem_manager.py sets list
    python problem_manager.py sets add
    python problem_manager.py sets remove <set_id>

  問題管理（セット内）
    python problem_manager.py questions list   <set_id>
    python problem_manager.py questions show   <set_id> <question_id>
    python problem_manager.py questions add    <set_id>
    python problem_manager.py questions remove <set_id> <question_id>
"""

import json
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).parent
REGISTRY_PATH = BASE_DIR / "problems.json"
SETS_DIR = BASE_DIR / "sets"

VALID_DIFFICULTIES = ["初級", "中級", "上級"]

# 入力値の上限
MAX_QUESTION_LEN = 500
MAX_CODE_LEN = 2000
MAX_CHOICE_LEN = 200
MAX_EXPLANATION_LEN = 1000
MAX_CHOICES = 8
MIN_CHOICES = 2


# ── ヘルパー ─────────────────────────────────────────────

def load_registry():
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return []


def save_registry(reg):
    REGISTRY_PATH.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")


def find_set(set_id):
    return next((s for s in load_registry() if s["id"] == set_id), None)


def load_questions(file_rel):
    path = BASE_DIR / file_rel
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_questions(file_rel, questions):
    path = BASE_DIR / file_rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")


def next_question_id(questions):
    return max((q["id"] for q in questions), default=0) + 1


def validate_question(q):
    if not q.get("question"):
        raise ValueError("question は必須です")
    if len(q["question"]) > MAX_QUESTION_LEN:
        raise ValueError(f"question が長すぎます（最大 {MAX_QUESTION_LEN} 文字）")
    if len(q.get("code", "")) > MAX_CODE_LEN:
        raise ValueError(f"code が長すぎます（最大 {MAX_CODE_LEN} 文字）")
    choices = q.get("choices", [])
    if not (MIN_CHOICES <= len(choices) <= MAX_CHOICES):
        raise ValueError(f"選択肢は {MIN_CHOICES}〜{MAX_CHOICES} 個にしてください")
    for c in choices:
        if len(c) > MAX_CHOICE_LEN:
            raise ValueError(f"選択肢が長すぎます（最大 {MAX_CHOICE_LEN} 文字）")
    answer = q.get("answer")
    if not isinstance(answer, int) or not (1 <= answer <= len(choices)):
        raise ValueError(f"answer は 1〜{len(choices)} の整数にしてください")
    if len(q.get("explanation", "")) > MAX_EXPLANATION_LEN:
        raise ValueError(f"explanation が長すぎます（最大 {MAX_EXPLANATION_LEN} 文字）")


# ── セット管理コマンド ────────────────────────────────────

def sets_list():
    reg = load_registry()
    if not reg:
        print("問題集が登録されていません。")
        return
    print(f"{'ID':<20} {'難易度':<6} {'問題数':>5}  タイトル")
    print("-" * 60)
    for s in reg:
        qs = load_questions(s["file"])
        count = len(qs)
        print(f"{s['id']:<20} {s.get('difficulty',''):<6} {count:>5}  {s['title']}")
    print(f"\n合計: {len(reg)} セット")


def sets_add():
    print("=== 問題集セットを追加 ===")
    set_id = input("セットID（英数字・アンダーバー）: ").strip()
    if not set_id or not set_id.replace("_", "").isalnum():
        print("有効なIDを入力してください（英数字とアンダーバーのみ）。中止します。")
        return
    if find_set(set_id):
        print(f"ID '{set_id}' は既に登録されています。")
        return

    title = input("タイトル: ").strip()
    if not title:
        print("タイトルは必須です。中止します。")
        return

    description = input("説明（省略可）: ").strip()

    print(f"難易度 {VALID_DIFFICULTIES}: ", end="")
    difficulty = input().strip()
    if difficulty not in VALID_DIFFICULTIES:
        print(f"難易度は {VALID_DIFFICULTIES} のいずれかにしてください。中止します。")
        return

    file_rel = f"sets/{set_id}.json"
    entry = {
        "id": set_id,
        "title": title,
        "description": description,
        "difficulty": difficulty,
        "file": file_rel,
    }

    # 空の問題ファイルを作成
    save_questions(file_rel, [])

    reg = load_registry()
    reg.append(entry)
    save_registry(reg)
    print(f"\n追加しました。問題は以下で登録できます:")
    print(f"  python problem_manager.py questions add {set_id}")


def sets_remove(set_id):
    reg = load_registry()
    target = find_set(set_id)
    if not target:
        print(f"ID '{set_id}' は見つかりませんでした。")
        return
    confirm = input(f"'{target['title']}' を削除しますか？ (y/N): ").strip().lower()
    if confirm != "y":
        print("中止しました。")
        return
    reg = [s for s in reg if s["id"] != set_id]
    save_registry(reg)
    print(f"レジストリから削除しました（問題ファイル {target['file']} は残ります）。")


# ── 問題管理コマンド ──────────────────────────────────────

def questions_list(set_id):
    target = find_set(set_id)
    if not target:
        print(f"セット '{set_id}' は見つかりませんでした。")
        return
    qs = load_questions(target["file"])
    if not qs:
        print("問題が登録されていません。")
        return
    print(f"【{target['title']}】 全 {len(qs)} 問")
    print(f"{'ID':>4}  問題")
    print("-" * 50)
    for q in qs:
        preview = q["question"][:44] + ("…" if len(q["question"]) > 44 else "")
        print(f"{q['id']:>4}  {preview}")


def questions_show(set_id, question_id):
    target = find_set(set_id)
    if not target:
        print(f"セット '{set_id}' は見つかりませんでした。")
        return
    qs = load_questions(target["file"])
    q = next((q for q in qs if q["id"] == question_id), None)
    if not q:
        print(f"問題 ID {question_id} は見つかりませんでした。")
        return
    print(f"ID: {q['id']}")
    print(f"問題: {q['question']}")
    if q.get("code"):
        print(f"コード:\n{q['code']}")
    print("選択肢:")
    for i, c in enumerate(q["choices"], 1):
        mark = " ← 正解" if i == q["answer"] else ""
        print(f"  {i}: {c}{mark}")
    if q.get("explanation"):
        print(f"解説: {q['explanation']}")


def questions_add(set_id):
    target = find_set(set_id)
    if not target:
        print(f"セット '{set_id}' は見つかりませんでした。")
        return

    print(f"=== 【{target['title']}】に問題を追加 ===")
    question = input("問題文: ").strip()
    if not question:
        print("問題文は必須です。中止します。")
        return

    print("コードを入力（複数行可、空行で終了。不要なら最初から空行）:")
    code_lines = []
    while True:
        line = input()
        if line == "" and not code_lines:
            break
        if line == "" and code_lines and code_lines[-1] == "":
            code_lines.pop()
            break
        code_lines.append(line)
    code = "\n".join(code_lines)

    choices = []
    print(f"選択肢を入力（{MIN_CHOICES}〜{MAX_CHOICES} 個、空Enterで終了）:")
    for i in range(1, MAX_CHOICES + 1):
        c = input(f"  選択肢{i}: ").strip()
        if not c:
            break
        choices.append(c)

    if len(choices) < MIN_CHOICES:
        print(f"選択肢は {MIN_CHOICES} つ以上必要です。中止します。")
        return

    print("\n入力した選択肢:")
    for i, c in enumerate(choices, 1):
        print(f"  {i}: {c}")
    answer_str = input("正解の番号: ").strip()
    try:
        answer = int(answer_str)
        if not (1 <= answer <= len(choices)):
            raise ValueError()
    except ValueError:
        print(f"正解は 1〜{len(choices)} の整数で入力してください。中止します。")
        return

    explanation = input("解説（省略可）: ").strip()

    qs = load_questions(target["file"])
    entry = {
        "id": next_question_id(qs),
        "question": question,
        "code": code,
        "choices": choices,
        "answer": answer,
        "explanation": explanation,
    }
    try:
        validate_question(entry)
    except ValueError as e:
        print(f"入力エラー: {e}")
        return

    qs.append(entry)
    save_questions(target["file"], qs)
    print(f"\n追加しました（ID={entry['id']}）。")


def questions_remove(set_id, question_id):
    target = find_set(set_id)
    if not target:
        print(f"セット '{set_id}' は見つかりませんでした。")
        return
    qs = load_questions(target["file"])
    before = len(qs)
    qs = [q for q in qs if q["id"] != question_id]
    if len(qs) == before:
        print(f"問題 ID {question_id} は見つかりませんでした。")
    else:
        save_questions(target["file"], qs)
        print(f"ID {question_id} を削除しました。")


# ── エントリポイント ──────────────────────────────────────

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="模擬試験 問題集管理ツール")
    sub = p.add_subparsers(dest="group")

    # --- sets ---
    sets_p = sub.add_parser("sets", help="問題集セットの管理")
    sets_sub = sets_p.add_subparsers(dest="cmd")
    sets_sub.add_parser("list", help="セット一覧")
    sets_sub.add_parser("add", help="セットを追加")
    sets_rm = sets_sub.add_parser("remove", help="セットを削除")
    sets_rm.add_argument("set_id")

    # --- questions ---
    q_p = sub.add_parser("questions", help="問題の管理")
    q_sub = q_p.add_subparsers(dest="cmd")

    q_list = q_sub.add_parser("list", help="問題一覧")
    q_list.add_argument("set_id")

    q_show = q_sub.add_parser("show", help="問題の詳細（正解含む）")
    q_show.add_argument("set_id")
    q_show.add_argument("question_id", type=int)

    q_add = q_sub.add_parser("add", help="問題を追加")
    q_add.add_argument("set_id")

    q_rm = q_sub.add_parser("remove", help="問題を削除")
    q_rm.add_argument("set_id")
    q_rm.add_argument("question_id", type=int)

    args = p.parse_args()

    if args.group == "sets":
        if args.cmd == "list":
            sets_list()
        elif args.cmd == "add":
            sets_add()
        elif args.cmd == "remove":
            sets_remove(args.set_id)
        else:
            sets_p.print_help()
    elif args.group == "questions":
        if args.cmd == "list":
            questions_list(args.set_id)
        elif args.cmd == "show":
            questions_show(args.set_id, args.question_id)
        elif args.cmd == "add":
            questions_add(args.set_id)
        elif args.cmd == "remove":
            questions_remove(args.set_id, args.question_id)
        else:
            q_p.print_help()
    else:
        p.print_help()
