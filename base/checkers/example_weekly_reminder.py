"""【Lv1｜定期リマインド】決まった曜日・日付に思い出させる。

外部のサービスと繋がなくていい、**いちばん簡単な型**。
LINEとGitHubの設定さえ済んでいれば、ここを書き換えるだけで動きます。

例：「毎週火曜は子どもの薬」「毎月25日は請求書」「毎月1日は家賃の振込確認」

このファイルは**実例**です。自分用に書き換えるか、要らなければ削除してください。
"""

from datetime import date

TITLE = "🔔 今日のリマインド"

#: weekday … 月=0 火=1 水=2 木=3 金=4 土=5 日=6
#: day     … 毎月のこの日（1〜31）
#: month_day … 毎年のこの日（"MM-DD"）
REMINDERS = [
    {"weekday": 1, "text": "子どもにK2シロップを飲ませる日です"},
    {"day": 25, "text": "請求書の送付日です"},
    {"day": 1, "text": "先月分の経費をまとめる日です"},
    {"month_day": "04-01", "text": "年度はじめです。契約の見直しを"},
]


def run(today: date, state: dict):
    hits = []

    for r in REMINDERS:
        if "weekday" in r and today.weekday() == r["weekday"]:
            hits.append(r["text"])
        elif "day" in r and today.day == r["day"]:
            hits.append(r["text"])
        elif "month_day" in r and today.strftime("%m-%d") == r["month_day"]:
            hits.append(r["text"])

    if not hits:
        return None

    lines = [TITLE, ""]
    lines += [f"・{h}" for h in hits]
    return "\n".join(lines)
