"""【Lv3-a｜新着チェック】RSSを見て、前回から増えたものだけ知らせる。

**通知済みの記録（state）を使う型**です。これがないと、毎朝同じ記事が届きます。

「ブログの更新」「ニュースサイト」「GitHubのリリース」など、RSSがあるものなら何でも。
RSSが無いサービスでも、APIがあれば同じ形で書けます（取ってくる部分だけ差し替える）。

■ 相手のサーバーへの配慮
1日1回、数件のフィードを読むだけにしてください。
短い間隔で何度も叩かないこと。

このファイルは**実例**です。自分用に書き換えるか、要らなければ削除してください。
"""

import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import state as state_mod  # noqa: E402

TITLE = "📰 新着"

#: このチェッカーの名前。state の中でこの名前の箱に記録されます
KEY = "rss_new"

#: 見にいくRSS。{名前: URL}
FEEDS = {
    "はてなブックマーク（テクノロジー）": "https://b.hatena.ne.jp/hotentry/it.rss",
}

#: 1回に知らせる上限（多すぎると見なくなるため）
MAX_ITEMS = 5


def _fetch(url: str) -> list[tuple[str, str]]:
    """RSS/Atom から (タイトル, リンク) を取り出す。読めなければ空リスト。"""
    res = requests.get(url, timeout=20, headers={"User-Agent": "line-notify-kit/1.0"})
    res.raise_for_status()
    root = ET.fromstring(res.content)

    items = []

    # RSS 2.0 / RSS 1.0
    for item in root.iter():
        tag = item.tag.split("}")[-1]
        if tag != "item":
            continue
        title = link = ""
        for child in item:
            ctag = child.tag.split("}")[-1]
            if ctag == "title":
                title = (child.text or "").strip()
            elif ctag == "link":
                link = (child.text or "").strip()
        if title and link:
            items.append((title, link))

    # Atom
    if not items:
        for entry in root.iter():
            if entry.tag.split("}")[-1] != "entry":
                continue
            title = link = ""
            for child in entry:
                ctag = child.tag.split("}")[-1]
                if ctag == "title":
                    title = (child.text or "").strip()
                elif ctag == "link":
                    link = (child.attrib.get("href") or "").strip()
            if title and link:
                items.append((title, link))

    return items


def run(today: date, state: dict):
    blocks = []

    for name, url in FEEDS.items():
        try:
            items = _fetch(url)
        except Exception as e:  # noqa: BLE001
            # 1つ落ちても他のフィードは見る。理由は通知に出す
            blocks.append(f"⚠️ {name} を取得できませんでした（{type(e).__name__}）")
            continue

        fresh = []
        for title, link in items:
            if not state_mod.is_new(state, KEY, link):
                continue
            fresh.append((title, link))
            # ⚠️ ここで記録しても、run.py は「送信が成功したときだけ」state を保存する。
            #    失敗した回の分は次回もう一度通知される（取りこぼすよりよい）
            state_mod.mark_seen(state, KEY, link)
            if len(fresh) >= MAX_ITEMS:
                break

        if not fresh:
            continue

        lines = [f"{TITLE}｜{name}（{len(fresh)}件）", ""]
        for title, link in fresh:
            lines.append(f"・{title}")
            lines.append(f"　{link}")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks) if blocks else None
