# line-notify-kit（LINE通知キット）

**自分専用のLINE通知を作れる土台。** GitHub Actions が毎日動き、`checkers/` にある通知を
全部まわして1通にまとめて送る。RISEのAI自動化講座のコンテンツ用。

**解説ページ： https://ryoya9595.github.io/line-notify-kit/**

## 方針

- **毎日の実行にAIを使わない。** 設置後は GitHub だけで動く（導入にはClaude CodeかCodexの有料プランが要る）
- **checkers/ に置くだけで増える。** 登録作業なし
- **何本増えても届くのは1通**
- **通知することが無い日は送らない**
- **1本が落ちても他は動く**（例外は ⚠️ として本文に出る）
- 何を作るかは導入時にヒアリングして決める。**最初は1本だけ**

## 3つのキットの関係

| 器 | 向いている型 | 必要なもの | キット |
|---|---|---|---|
| **GitHub Actions** | 定期リマインド／記念日・期限／新着チェック／集計／突合 | GitHubのみ | **これ** |
| AIのルーティン | AIが探して選ぶ（案件・情報収集） | Claude Pro以上 | [anken-watch](https://ryoya9595.github.io/anken-watch/) |
| Vercel Webhook | LINEから登録・操作 | Vercel | [tanjobi-line](https://ryoya9595.github.io/tanjobi-line/) |

型カタログ（Lv1〜6）は `通知の型カタログ.md`。これが講座の章立てにあたる。

## 構成

```
GitHub Actions（毎朝・cron）
   ↓ run.py
   ├ checkers/*.py を自動で読み込む（_ 始まりは除く）
   ├ 各 run(today, state) を呼ぶ  ← 1本落ちても他は続行
   ├ 戻り値が文字列のものだけ集める（None は無視）
   ↓ 1通にまとめる（区切り線でつなぐ）
   ↓ notify.py → LINE push
   ↓ 送信が成功したときだけ state.json を保存・commit
```

| ファイル | 役割 |
|---|---|
| `base/run.py` | 全体をまわす。完成品 |
| `base/notify.py` | LINE送信。完成品 |
| `base/state.py` | 通知済みの記録。完成品 |
| `base/checkers/_template.py` | チェッカーの雛形 |
| `base/checkers/example_*.py` | Lv1・Lv2・Lv3a の実例 |
| `base/dev/test_base.py` | 土台の検証（リポジトリに配置後も動く場所に置いてある） |
| `通知の型カタログ.md` | **6つの型**。講座の章立て |
| `何を通知するか決めるシート.md` | 導入時のヒアリング |

## 開発

```bash
python3 base/dev/test_base.py
```

チェッカーの読み込み（`_` 始まりの無視・`run` が無いものの扱い）、例外が出ても他が動くか、
`None`／空文字を返したものが通知に入らないか、通知済みの記録（上限・間引き・壊れたJSONからの復帰）、
設定の検証、長文の分割を確認する。ネットにもLINEにも接続しない。

手元で試す：

```bash
cd base
python3 run.py --list
python3 run.py --dry-run --date 2026-09-22
python3 run.py --only example_weekly_reminder --dry-run
```

配布Zipを作り直す：

```bash
bash dev/build_zip.sh
```

## チェッカーの約束

```python
TITLE = "見出し"

def run(today, state):
    # 通知したいことがあれば文字列を返す。無ければ None
    return None
```

- **通知することが無い日は必ず `None`。** 「今日はありません」を返すと毎日それが届く
- `state` を使う型（新着チェック）では、記録を**送信の前に確定させない**。
  `run.py` は送信が成功したときだけ `state.json` を保存する

## 仕様メモ

- `checkers/` は `run.py` が glob で読む。`_` 始まりは対象外（テンプレートがそれ）
- 1本が例外を出しても `collect()` が握って ⚠️ として本文に載せる。他のチェッカーは動く
- `state.py` は1チェッカーあたり500件まで記録し、古いものから捨てる
- workflow は `permissions: contents: write`（`state.json` の書き戻し用）
- 実行時刻は GitHub Actions の仕様で混雑時に数十分ずれる

## 配布時の注意

- 通知の中身に個人情報が入るなら、リポジトリは **Private**
- 使わない `example_*.py` は削除させる（残すと余計な通知が届く）
- cron はUTC。曜日もずれる（日本の月〜金＝UTCの `0-4`）
