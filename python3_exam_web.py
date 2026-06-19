from flask import Flask, render_template, request, redirect, url_for, session
import json
import random
from pathlib import Path

app = Flask(__name__, template_folder="templates")
app.secret_key = "change_this_to_a_random_secret"

BASE_DIR = Path(__file__).parent


def load_registry():
    path = BASE_DIR / "problems.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_question_set(file_rel):
    path = BASE_DIR / file_rel
    data = json.loads(path.read_text(encoding="utf-8"))
    return {q["id"]: q for q in data}


def get_set_info(set_id):
    for s in load_registry():
        if s["id"] == set_id:
            return s
    return None


def current_questions():
    set_id = session.get("set_id")
    if not set_id:
        return {}
    info = get_set_info(set_id)
    if not info:
        return {}
    return load_question_set(info["file"])


@app.route("/")
def index():
    registry = load_registry()
    for s in registry:
        try:
            qs = load_question_set(s["file"])
            s["count"] = len(qs)
        except Exception:
            s["count"] = "?"
    return render_template("index.html", sets=registry)


@app.route("/start")
def start():
    set_id = request.args.get("set_id")
    info = get_set_info(set_id)
    if not info:
        return redirect(url_for("index"))
    questions = load_question_set(info["file"])
    order = list(questions.keys())
    random.shuffle(order)
    session.clear()
    session["set_id"] = set_id
    session["order"] = order
    session["current"] = 0
    session["score"] = 0
    session["history"] = []
    return redirect(url_for("quiz"))


@app.route("/quiz")
def quiz():
    questions = current_questions()
    order = session.get("order")
    current = session.get("current", 0)
    if not order or current >= len(order):
        return redirect(url_for("result"))
    qid = order[current]
    question = questions[qid]

    choice_order = list(range(len(question["choices"])))
    random.shuffle(choice_order)
    shuffled_choices = [question["choices"][i] for i in choice_order]
    session[f"choice_order_{qid}"] = choice_order

    set_info = get_set_info(session.get("set_id")) or {}
    return render_template(
        "question.html",
        question=question,
        qid=qid,
        current=current + 1,
        total=len(order),
        shuffled_choices=shuffled_choices,
        set_title=set_info.get("title", ""),
    )


@app.route("/answer", methods=["POST"])
def answer():
    questions = current_questions()
    order = session.get("order")
    current = session.get("current", 0)
    if not order or current >= len(order):
        return redirect(url_for("index"))

    qid = int(request.form["qid"])
    selected_index = int(request.form.get("choice"))
    question = questions[qid]
    choice_order = session.get(f"choice_order_{qid}", list(range(len(question["choices"]))))
    selected = question["choices"][choice_order[selected_index]]
    correct = question["choices"][question["answer"] - 1]
    is_correct = selected == correct

    history = session.get("history", [])
    history.append({
        "qid": qid,
        "selected": selected,
        "correct": correct,
        "is_correct": is_correct,
    })
    session["history"] = history

    if is_correct:
        session["score"] = session.get("score", 0) + 1

    session["current"] = current + 1
    session.pop(f"choice_order_{qid}", None)
    next_label = "結果を見る" if session["current"] >= len(order) else "次の問題へ"
    next_url = url_for("result") if session["current"] >= len(order) else url_for("quiz")

    explanation = question.get("explanation", "")
    return render_template(
        "answer.html",
        selected=selected,
        correct=correct,
        is_correct=is_correct,
        explanation=explanation,
        score=session.get("score", 0),
        total=len(order),
        next_label=next_label,
        next_url=next_url,
    )


@app.route("/result")
def result():
    order = session.get("order", [])
    answered = session.get("current", 0)
    total = len(order)
    finished = answered >= total and total > 0
    history = session.get("history", [])
    questions = current_questions()
    set_info = get_set_info(session.get("set_id")) or {}
    return render_template(
        "result.html",
        score=session.get("score", 0),
        total=total,
        answered=answered,
        finished=finished,
        history=history,
        python_mock_exam=questions,
        set_info=set_info,
    )


@app.route("/help")
def help_page():
    return render_template("help.html")


@app.route("/problem_detail/<int:qid>")
def problem_detail(qid):
    history = session.get("history", [])
    problem_data = next((h for h in history if h["qid"] == qid), None)
    if not problem_data:
        return redirect(url_for("result"))
    questions = current_questions()
    question = questions.get(qid)
    if not question:
        return redirect(url_for("result"))
    return render_template(
        "problem_detail.html",
        qid=qid,
        question=question,
        selected=problem_data["selected"],
        correct=problem_data["correct"],
        is_correct=problem_data["is_correct"],
    )


if __name__ == "__main__":
    app.run(debug=True)
