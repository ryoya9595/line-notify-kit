"""checkers/ にある通知を全部まわして、1通のLINEにまとめて送る。

**このファイルは完成品です。触らなくて構いません。**
通知を増やしたいときは `checkers/` にファイルを1つ足すだけです。
足したファイルは自動で見つかります（登録作業は要りません）。

■ 動作確認
    python3 run.py --list                  どのチェッカーがあるか見る
    python3 run.py --dry-run               送らずに、届く内容を表示する
    python3 run.py --dry-run --date 2026-06-23   その日で試す
    python3 run.py --only birthday --dry-run     1本だけ試す

■ 設計のきまり
- **1本がエラーになっても、他は動かす。** 失敗したものは ⚠️ として本文に出す
  （通知が丸ごと来なくなるより、1行壊れて届くほうがよい）
- **通知することが何もない日は、何も送らない。** 毎日届くと見なくなるため
- **state.json は送信が成功したときだけ保存する。** 失敗した回の分は次回もう一度通知される
  （取りこぼすより、まれに重複するほうがよい）
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import notify  # noqa: E402
import state as state_mod  # noqa: E402

JST = timezone(timedelta(hours=9))
CHECKERS_DIR = HERE / "checkers"
SEPARATOR = "\n\n━━━━━━━━\n\n"


def today_jst() -> date:
    return datetime.now(JST).date()


# ------------------------------------------------------------------ 読み込み

def load_checkers(only: str | None = None) -> list:
    """checkers/ の中の .py を読み込む。`_` で始まるファイルは無視する。"""
    found = []
    for path in sorted(CHECKERS_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        name = path.stem
        if only and only != name:
            continue

        spec = importlib.util.spec_from_file_location(f"checkers.{name}", path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception:
            print(f"[{name}] 読み込みに失敗しました")
            traceback.print_exc()
            found.append(("error", name, getattr(module, "TITLE", name), None))
            continue

        if not hasattr(module, "run"):
            print(f"[{name}] run(today, state) がないので飛ばします")
            continue

        found.append(("ok", name, getattr(module, "TITLE", name), module))
    return found


# ------------------------------------------------------------------ 実行

def collect(today: date, state: dict, only: str | None = None) -> list[str]:
    """各チェッカーを動かして、通知したい文章だけを集める。"""
    blocks: list[str] = []

    for status, name, title, module in load_checkers(only):
        if status == "error":
            blocks.append(f"⚠️ {title}\nプログラムの読み込みに失敗しました（{name}.py）")
            continue

        try:
            result = module.run(today, state)
        except Exception as e:  # noqa: BLE001
            print(f"[{name}] 実行中にエラー")
            traceback.print_exc()
            blocks.append(f"⚠️ {title}\nエラーが出ました: {type(e).__name__}: {e}")
            continue

        if not result:
            print(f"[{name}] 通知なし")
            continue

        text = result.strip() if isinstance(result, str) else str(result)
        if text:
            print(f"[{name}] 通知あり（{len(text)}文字）")
            blocks.append(text)

    return blocks


def main() -> int:
    ap = argparse.ArgumentParser(description="checkers/ をまわしてLINEに通知する")
    ap.add_argument("--date", help="この日で判定する（例 2026-06-23）")
    ap.add_argument("--dry-run", action="store_true", help="送らずに内容を表示する")
    ap.add_argument("--only", help="このチェッカーだけ動かす（ファイル名から .py を取ったもの）")
    ap.add_argument("--list", action="store_true", help="チェッカーの一覧を表示する")
    args = ap.parse_args()

    if args.list:
        rows = load_checkers()
        if not rows:
            print("checkers/ にまだ何もありません。_template.py をコピーして作ってください。")
            return 0
        print(f"チェッカー {len(rows)}本:")
        for status, name, title, _ in rows:
            mark = "  " if status == "ok" else "⚠️"
            print(f"  {mark} {name:28s} {title}")
        return 0

    if args.date:
        try:
            today = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"日付として読めません: {args.date}（例 2026-06-23）")
            return 1
    else:
        today = today_jst()

    state = state_mod.load()
    blocks = collect(today, state, args.only)

    if not blocks:
        print(f"[{today}] 通知することはありませんでした。何も送りません。")
        return 0

    body = SEPARATOR.join(blocks)

    if args.dry_run:
        print("\n--- 送られる内容 ---")
        print(body)
        print("--------------------")
        return 0

    problems = notify.check_config()
    if problems:
        print("設定に問題があります:")
        for p in problems:
            print(f"  - {p}")
        return 1

    ok, message = notify.push(body)
    print(message)

    if ok:
        # 送信が成功したときだけ記録を確定させる
        state_mod.save(state)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
