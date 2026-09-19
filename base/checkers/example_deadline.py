"""【Lv2｜期限の監視】期限が近いものだけ知らせる。終わったら外す。

一覧（CSV）を持っておいて、期限が近づいたものだけ通知します。
「ドメインの更新」「契約の満了」「資格の更新」「無料期間の終了」など。

■ 一覧の形（data/deadlines.csv）
    name,date,memo
    example.com の更新,2026-11-30,自動更新オフ済み
    ○○の契約満了,2026-12-15,更新するか要検討

■ 終わったものを外すには
CSVからその行を消します。完了コマンドを作りたい場合は、
LINEから操作する型（Lv6）と組み合わせます。

このファイルは**実例**です。自分用に書き換えるか、要らなければ削除してください。
"""

import csv
from datetime import date, datetime
from pathlib import Path

TITLE = "⏰ 期限が近いもの"

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "deadlines.csv"

#: 何日前から知らせるか。複数指定できる（この日数ちょうどのときだけ鳴る）
NOTIFY_DAYS_BEFORE = [30, 14, 7, 3, 1, 0]


def _parse(value: str):
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def run(today: date, state: dict):
    if not CSV_PATH.exists():
        # 一覧がまだ無いだけ。エラーにはしない
        return None

    hits = []
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("name") or "").strip()
            due = _parse(row.get("date") or "")
            if not name or due is None:
                continue

            days_left = (due - today).days
            if days_left not in NOTIFY_DAYS_BEFORE:
                continue

            memo = (row.get("memo") or "").strip()
            if days_left == 0:
                # LINEは太字などの装飾に対応していないので、記号で目立たせる
                when = "⚠️ 今日が期限"
            else:
                when = f"あと{days_left}日（{due.strftime('%-m/%-d')}）"
            hits.append((days_left, name, when, memo))

    if not hits:
        return None

    hits.sort()
    lines = [f"{TITLE}（{len(hits)}件）", ""]
    for _, name, when, memo in hits:
        lines.append(f"・{name}")
        lines.append(f"　{when}" + (f"｜{memo}" if memo else ""))
    return "\n".join(lines)
