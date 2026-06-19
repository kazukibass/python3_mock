import json
import random
from pathlib import Path

BASE_DIR = Path(__file__).parent


def load_registry():
    path = BASE_DIR / "problems.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_question_set(file_rel):
    path = BASE_DIR / file_rel
    data = json.loads(path.read_text(encoding="utf-8"))
    return {q["id"]: q for q in data}


def select_set():
    registry = load_registry()
    if not registry:
        print("問題集が登録されていません。")
        return None
    if len(registry) == 1:
        return registry[0]
    print("\n== 問題集を選んでください ==\n")
    for i, s in enumerate(registry, 1):
        qs = load_question_set(s["file"])
        print(f"  {i}. [{s.get('difficulty','')}] {s['title']}  ({len(qs)}問)  {s.get('description','')}")
    while True:
        choice = input("\n番号を入力: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(registry):
                return registry[idx]
        except ValueError:
            pass
        print(f"1〜{len(registry)} で入力してください。")


def print_question(question):
    print(question["question"])
    if question.get("code"):
        print(question["code"])
    pre_list = list(range(len(question["choices"])))
    choice_order = random.sample(pre_list, len(pre_list))
    display = {}
    for c, orig_idx in enumerate(choice_order, 1):
        print(f"{c}:{question['choices'][orig_idx]}")
        display[c] = question["choices"][orig_idx]
    user_answer = input_user_answer(len(choice_order))
    return display[user_answer]


def check_answer(question, ans):
    correct = question["choices"][question["answer"] - 1]
    print("--------------------------------------------------")
    if correct == ans:
        print(f"  あなたの回答:「{ans}」")
        print("  ★ 正解！")
        result = 1
    else:
        print(f"  あなたの回答:「{ans}」")
        print("  × 不正解")
        print(f"  正解は →「{correct}」")
        result = 0
    explanation = question.get("explanation", "")
    if explanation:
        print(f"  【解説】{explanation}")
    print("--------------------------------------------------")
    return result


def input_user_answer(num_choices):
    while True:
        raw = input(f"回答を入力してください（1〜{num_choices}）: ")
        try:
            val = int(raw)
            if 1 <= val <= num_choices:
                return val
        except ValueError:
            pass
        print(f"1〜{num_choices} の数字で入力してください。")


def print_result_list(history):
    if not history:
        return
    correct_count = sum(1 for e in history if e["is_correct"])
    print("\n" + "=" * 55)
    print(f"  解答一覧  （正解 {correct_count} / {len(history)} 問）")
    print("=" * 55)
    for entry in history:
        if entry["is_correct"]:
            mark = "★ 正解"
        else:
            mark = "× 不正解"
        print(f"\n  第{entry['num']}問 [{mark}]")
        print(f"  問題: {entry['question_preview']}")
        if entry["code_preview"]:
            first_line = entry["code_preview"].split("\n")[0]
            suffix = "…" if "\n" in entry["code_preview"] else ""
            print(f"  コード: {first_line}{suffix}")
        if entry["is_correct"]:
            print(f"  回答: 「{entry['user_answer']}」")
        else:
            print(f"  回答: 「{entry['user_answer']}」  →  正解:「{entry['correct_answer']}」")
        if entry["explanation"]:
            print(f"  【解説】{entry['explanation']}")
        print("  " + "-" * 51)
    print("=" * 55)


def run_console_quiz():
    set_info = select_set()
    if not set_info:
        return
    questions = load_question_set(set_info["file"])
    print(f"\n【{set_info['title']}】スタート！  全{len(questions)}問\n")

    order = random.sample(list(questions.keys()), len(questions))
    win = 0
    history = []
    try:
        for c, qid in enumerate(order, 1):
            question = questions[qid]
            print(f"第{c}問:")
            user_ans = print_question(question)
            correct = question["choices"][question["answer"] - 1]
            is_correct = check_answer(question, user_ans)
            win += is_correct
            code = question.get("code", "")
            history.append({
                "num": c,
                "question_preview": question["question"][:40] + ("…" if len(question["question"]) > 40 else ""),
                "code_preview": code,
                "user_answer": user_ans,
                "correct_answer": correct,
                "is_correct": bool(is_correct),
                "explanation": question.get("explanation", ""),
            })
    except KeyboardInterrupt:
        print("\n\n-- 中断されました --")

    print(f"\nあなたの正解数は {win}/{len(history)} 問！")
    print_result_list(history)


if __name__ == "__main__":
    run_console_quiz()
