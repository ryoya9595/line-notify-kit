"""土台（run.py / state.py / notify.py）の検証（納品物ではない）。

    python3 dev/test_base.py

LINEにもネットにも接続しない。base/ を直したら必ず実行する。
"""

import json
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

# base/dev/ に置かれている。親が土台（run.py などがある場所）
BASE = Path(__file__).resolve().parent.parent
ROOT = BASE

sys.path.insert(0, str(BASE))
import state as state_mod  # noqa: E402
import notify  # noqa: E402

NG = 0


def ok(label, actual, expected):
    global NG
    if actual == expected:
        print(f"  ok   {label}")
    else:
        NG += 1
        print(f"  NG   {label}\n       期待 {expected!r}\n       実際 {actual!r}")


# ------------------------------------------------------------------ state

print("\n■ 通知済みの記録（state）")
st = {}
ok("最初は新しい扱い", state_mod.is_new(st, "foo", "a1"), True)
state_mod.mark_seen(st, "foo", "a1")
ok("記録すると新しくない", state_mod.is_new(st, "foo", "a1"), False)
ok("別のIDは新しいまま", state_mod.is_new(st, "foo", "a2"), True)
ok("別のチェッカーには影響しない", state_mod.is_new(st, "bar", "a1"), True)
state_mod.mark_seen(st, "foo", "a1")
ok("二重に記録しても増えない", len(st["foo"]["seen"]), 1)
ok("数値のIDも文字列として扱う", state_mod.is_new(st, "foo", 999), True)

st2 = {}
for i in range(state_mod.MAX_SEEN_PER_CHECKER + 50):
    state_mod.mark_seen(st2, "many", f"id{i}")
ok("上限を超えたら古いものから捨てる", len(st2["many"]["seen"]), state_mod.MAX_SEEN_PER_CHECKER)
ok("新しいものは残る", state_mod.is_new(st2, "many", f"id{state_mod.MAX_SEEN_PER_CHECKER + 49}"), False)
ok("古いものは忘れている", state_mod.is_new(st2, "many", "id0"), True)

print("\n■ 今日もう送ったかの記録")
st3 = {}
ok("最初は未送信", state_mod.already_sent_today(st3, "x", "2026-09-19"), False)
state_mod.mark_sent_today(st3, "x", "2026-09-19")
ok("記録すると送信済み", state_mod.already_sent_today(st3, "x", "2026-09-19"), True)
ok("日が変われば未送信", state_mod.already_sent_today(st3, "x", "2026-09-20"), False)

print("\n■ 保存と読み込み")
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "state.json"
    state_mod.save({"a": {"seen": ["1", "2"]}}, p)
    back = state_mod.load(p)
    ok("往復できる", back, {"a": {"seen": ["1", "2"]}})

    ok("ファイルが無ければ空", state_mod.load(Path(tmp) / "none.json"), {})

    p.write_text("こわれたJSON", encoding="utf-8")
    ok("壊れていても空で返す（止まらない）", state_mod.load(p), {})

# ------------------------------------------------------------------ notify

print("\n■ 長文の分割")
long_text = "\n".join(f"・{i}行目のテキストです" for i in range(600))
chunks = notify.split_text(long_text, 4500)
ok("分割される", len(chunks) > 1, True)
ok("各かたまりが上限内", all(len(c) <= 4500 for c in chunks), True)
ok("短ければ1つ", len(notify.split_text("みじかい", 4500)), 1)

print("\n■ 設定の検証（誤りを名指しできるか）")
import os  # noqa: E402

saved = {k: os.environ.get(k) for k in (notify.TOKEN_ENV, notify.USER_ID_ENV)}
try:
    os.environ.pop(notify.TOKEN_ENV, None)
    os.environ.pop(notify.USER_ID_ENV, None)
    problems = notify.check_config()
    ok("未設定を2件とも指摘する", len(problems), 2)

    os.environ[notify.TOKEN_ENV] = "みじかすぎる"
    os.environ[notify.USER_ID_ENV] = "U" + "x" * 32
    problems = notify.check_config()
    ok("短いトークンを指摘する", any("短すぎ" in p for p in problems), True)

    os.environ[notify.TOKEN_ENV] = "t" * 180
    os.environ[notify.USER_ID_ENV] = "1234567890"
    problems = notify.check_config()
    ok("ユーザーIDの形を指摘する", any("形が違" in p for p in problems), True)

    os.environ[notify.USER_ID_ENV] = "U" + "a" * 32
    ok("両方正しければ問題なし", notify.check_config(), [])
finally:
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v

print("\n■ エラーの説明が日本語になるか")
ok("401はトークン", "トークン" in notify.describe_error(401, ""), True)
ok("400は友だち追加に触れる", "友だち追加" in notify.describe_error(400, ""), True)
ok("429は無料枠", "無料" in notify.describe_error(429, ""), True)

# ------------------------------------------------------------------ run.py

print("\n■ チェッカーの読み込みと実行（run.py）")

TEMPLATES = {
    "ok_checker.py": '''
TITLE = "テスト通知"
def run(today, state):
    return "これは通知です"
''',
    "none_checker.py": '''
TITLE = "何も無い通知"
def run(today, state):
    return None
''',
    "empty_checker.py": '''
TITLE = "空文字を返す"
def run(today, state):
    return "   "
''',
    "boom_checker.py": '''
TITLE = "こわれた通知"
def run(today, state):
    raise ValueError("わざと失敗させています")
''',
    "norun_checker.py": '''
TITLE = "run が無い"
''',
    "_ignored.py": '''
TITLE = "読み込まれないはず"
def run(today, state):
    return "これは出てはいけない"
''',
}

with tempfile.TemporaryDirectory() as tmp:
    work = Path(tmp) / "base"
    shutil.copytree(BASE, work, ignore=shutil.ignore_patterns("checkers", "state.json", "__pycache__"))
    (work / "checkers").mkdir()
    for name, body in TEMPLATES.items():
        (work / "checkers" / name).write_text(body, encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(work / "run.py"), "--dry-run", "--date", "2026-09-19"],
        capture_output=True, text=True,
    )
    out = res.stdout

    ok("正常なチェッカーの内容が入る", "これは通知です" in out, True)
    ok("None を返したものは入らない", "何も無い通知" in out.split("送られる内容")[-1], False)
    ok("空白だけの戻り値も通知しない", "空文字を返す" in out.split("送られる内容")[-1], False)
    ok("_ 始まりは読み込まれない", "これは出てはいけない" in out, False)
    ok("例外が出ても他は動く", "これは通知です" in out, True)
    ok("例外は⚠️として本文に出る", "⚠️ こわれた通知" in out, True)
    ok("run が無いものは飛ばす", "run が無い" in out.split("送られる内容")[-1], False)
    ok("終了コードは0", res.returncode, 0)

    # 全部 None のときは「送らない」
    for name in list(TEMPLATES):
        (work / "checkers" / name).unlink()
    (work / "checkers" / "quiet.py").write_text(
        'TITLE = "静か"\ndef run(today, state):\n    return None\n', encoding="utf-8"
    )
    res = subprocess.run(
        [sys.executable, str(work / "run.py"), "--dry-run"], capture_output=True, text=True
    )
    ok("通知ゼロなら送らないと言う", "何も送りません" in res.stdout, True)
    ok("そのときも終了コードは0", res.returncode, 0)

    # --list
    res = subprocess.run([sys.executable, str(work / "run.py"), "--list"], capture_output=True, text=True)
    ok("--list が動く", "静か" in res.stdout, True)

print("\n✅ すべて通りました\n" if NG == 0 else f"\n❌ {NG}件 失敗しています\n")
sys.exit(0 if NG == 0 else 1)
