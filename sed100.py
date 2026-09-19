#!/usr/bin/env python3
"""sed 100本ノック: a terminal quiz app for practicing GNU sed."""
import argparse

from problems import PROBLEMS
from runner import run_sed, SedError
from progress import load_progress, save_progress, reset_progress

DIFFICULTY_STARS = {1: "*", 2: "**", 3: "***", 4: "****", 5: "*****"}


def render_block(text: str) -> str:
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    visible = [line.replace("\t", "[TAB]") for line in lines]
    return "\n".join(f"    {line}" for line in visible)


def print_problem(p: dict, index: int, total: int) -> None:
    print("=" * 60)
    print(f"[{index}/{total}] #{p['id']:03d}  {p['category']}  難易度:{DIFFICULTY_STARS[p['difficulty']]}")
    print(f"■ {p['title']}")
    print(p["description"])
    print("\n入力:")
    print(render_block(p["input"]))
    print("=" * 60)


def print_status(progress: dict) -> None:
    solved = progress.get("solved", {})
    total = len(PROBLEMS)
    done = sum(1 for pid, entry in solved.items() if entry.get("done"))
    print(f"\n進捗: {done}/{total} 問正解")
    categories: dict = {}
    for p in PROBLEMS:
        cat_stats = categories.setdefault(p["category"], [0, 0])
        cat_stats[1] += 1
        if solved.get(str(p["id"]), {}).get("done"):
            cat_stats[0] += 1
    for cat, (d, t) in categories.items():
        print(f"  {cat}: {d}/{t}")
    print()


def mark_solved(progress: dict, pid: int, attempts: int, revealed: bool) -> None:
    solved = progress.setdefault("solved", {})
    entry = solved.setdefault(str(pid), {"attempts": 0, "revealed": False, "done": False})
    entry["attempts"] += attempts
    entry["revealed"] = entry["revealed"] or revealed
    entry["done"] = True
    save_progress(progress)


def ask_problem(p: dict, progress: dict, index: int, total: int) -> str:
    """Run one problem interactively. Returns "solved", "skip", or "quit"."""
    print_problem(p, index, total)
    try:
        expected = run_sed(p["answer"], p["input"])
    except SedError as e:
        print(f"[内部エラー] 模範解答の実行に失敗しました: {e}")
        return "skip"

    attempts = 0
    revealed = False
    while True:
        try:
            user_input = input("\nsed > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n中断しました。進捗は保存されています。")
            return "quit"

        if not user_input:
            continue

        lowered = user_input.lower()
        if lowered in (":q", ":quit", ":exit"):
            return "quit"
        if lowered == ":skip":
            print("この問題をスキップしました。\n")
            return "skip"
        if lowered == ":hint":
            print(f"ヒント: {p['hint']}\n")
            continue
        if lowered == ":answer":
            print(f"模範解答: sed {p['answer']}\n")
            revealed = True
            continue
        if lowered == ":status":
            print_status(progress)
            continue

        attempts += 1
        try:
            actual = run_sed(user_input, p["input"])
        except SedError as e:
            print(f"sed エラー: {e}\n")
            continue

        if actual == expected:
            mark_solved(progress, p["id"], attempts, revealed)
            note = "（模範解答を確認済み）" if revealed else ""
            print(f"\n正解です！ 試行回数: {attempts} {note}\n")
            return "solved"

        print("\n不正解です。もう一度試してください。")
        print(f"  あなたの出力: {actual!r}")
        print(f"  期待する出力: {expected!r}\n")


def quiz_loop(problems: list, progress: dict) -> None:
    solved = progress.setdefault("solved", {})
    remaining = [p for p in problems if not solved.get(str(p["id"]), {}).get("done")]
    if not remaining:
        print("すべての問題に正解済みです。おめでとうございます！")
        print("--reset で進捗をリセットするか、--problem N で個別の問題を復習できます。")
        return

    for idx, p in enumerate(remaining, start=1):
        result = ask_problem(p, progress, idx, len(remaining))
        if result == "quit":
            print("進捗を保存して終了します。")
            return
    print("\nすべての問題が終了しました。お疲れ様でした！")


def print_intro() -> None:
    print("sed の100本ノックへようこそ。")
    print("各問題の「入力」に sed コマンドを適用し、「期待する出力」に一致させてください。")
    print("コマンドは実際のターミナルで `sed ` の後に続けて打つ内容をそのまま入力します（例: -n '2p'）。")
    print("空白を含むスクリプトは '...' のようにクォートしてください。")
    print("特殊コマンド: :hint (ヒント) / :answer (模範解答) / :skip (スキップ) / :status (進捗) / :quit (終了)\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="sed の100本ノック")
    parser.add_argument("--list", action="store_true", help="進捗一覧を表示する")
    parser.add_argument("--reset", action="store_true", help="進捗をリセットする")
    parser.add_argument("--problem", type=int, metavar="N", help="指定した番号の問題だけを解く")
    parser.add_argument("--category", type=str, metavar="NAME", help="指定したカテゴリの問題だけを解く")
    args = parser.parse_args()

    if args.reset:
        answer = input("進捗をすべてリセットします。よろしいですか？ (y/N): ").strip().lower()
        if answer == "y":
            reset_progress()
            print("進捗をリセットしました。")
        else:
            print("キャンセルしました。")
        return

    if args.list:
        print_status(load_progress())
        return

    progress = load_progress()
    print_intro()

    if args.problem is not None:
        target = [p for p in PROBLEMS if p["id"] == args.problem]
        if not target:
            print(f"問題番号 {args.problem} は存在しません（1〜{len(PROBLEMS)}）。")
            return
        ask_problem(target[0], progress, 1, 1)
        return

    if args.category is not None:
        target = [p for p in PROBLEMS if args.category in p["category"]]
        if not target:
            print(f"カテゴリ「{args.category}」に一致する問題が見つかりません。")
            return
        quiz_loop(target, progress)
        return

    quiz_loop(PROBLEMS, progress)


if __name__ == "__main__":
    main()
