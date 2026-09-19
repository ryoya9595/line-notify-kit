"""通知済みの記録（state.json）。

「同じものを二度通知しない」ためだけの、小さな保存場所です。

■ 使う型と使わない型
- Lv1 定期リマインド … だいたい不要（曜日で決まるため）
- Lv2 記念日・期限  … 「今日はもう送った」の記録に使う
- Lv3 新着チェック  … **必須**。どこまで読んだかを覚えておく
- Lv5 突合チェック  … 「この漏れはもう知らせた」の記録に使う

■ 保存される場所
リポジトリの `state.json`。GitHub Actions が実行のたびに commit して残します。
中身は「通知済みのID」だけで、本文は入れません（履歴に個人情報を残さないため）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STATE_PATH = Path(__file__).resolve().parent.parent / "state.json"

#: 1つのチェッカーが覚えておけるIDの上限。
#: 古いものから捨てる（無限に増えると state.json が膨らむため）
MAX_SEEN_PER_CHECKER = 500


def load(path: Path | None = None) -> dict[str, Any]:
    p = path or STATE_PATH
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        # 壊れていても止めない。空から作り直す（通知が重複するだけで済む）
        print(f"[state] 読み込みに失敗したので空から始めます: {e}")
        return {}


def save(state: dict[str, Any], path: Path | None = None) -> None:
    p = path or STATE_PATH
    p.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


# ------------------------------------------------------------------ 便利関数

def is_new(state: dict, checker: str, item_id: str) -> bool:
    """このIDをまだ通知していなければ True。"""
    return str(item_id) not in set(state.get(checker, {}).get("seen", []))


def mark_seen(state: dict, checker: str, item_id: str) -> None:
    """このIDを通知済みにする。**送信が成功したあとに呼ぶこと。**

    先に記録してしまうと、送信に失敗したときにその分が永久に通知されない。
    run.py は送信が成功したときだけ state を保存するので、
    チェッカーの中ではここを呼ぶだけでよい。
    """
    box = state.setdefault(checker, {}).setdefault("seen", [])
    sid = str(item_id)
    if sid in box:
        return
    box.append(sid)
    if len(box) > MAX_SEEN_PER_CHECKER:
        del box[: len(box) - MAX_SEEN_PER_CHECKER]


def already_sent_today(state: dict, checker: str, today: str) -> bool:
    """今日はもうこのチェッカーで通知したか。"""
    return state.get(checker, {}).get("last_sent") == today


def mark_sent_today(state: dict, checker: str, today: str) -> None:
    state.setdefault(checker, {})["last_sent"] = today


def get(state: dict, checker: str, key: str, default=None):
    """チェッカーごとの自由なメモ置き場（最後に見た日時など）。"""
    return state.get(checker, {}).get(key, default)


def put(state: dict, checker: str, key: str, value) -> None:
    state.setdefault(checker, {})[key] = value
