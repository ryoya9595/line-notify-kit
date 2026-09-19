# 【AIエージェントへの指示】LINE通知キットの導入

このファイルを読んだAI（Claude Code / Codex など）へ。**あなたが主導して**導入を進めてください。

担当者（人間）にやってもらうのは、原則として次の3つだけです。

1. **質問に答える**（何を通知したいか）
2. **ログイン**（LINE・GitHub）
3. **秘密の値の貼り付け**（チャネルアクセストークン）

それ以外——画面の遷移、ボタン操作、入力、ファイル配置、コマンド実行、チェッカーの作成——は、
使えるツールの範囲で**あなたが行います**。

> ⚠️ **絶対に守ること**
>
> - **確認を取る前に、外部サービスの状態を変えない。** 各STEPの冒頭で「これから○○します。進めてよいですか？」と聞く
> - 🔴 **いま使っているLINE公式アカウント（エルメ／Lステップ）には触らない。** 通知専用を**新規に作る**
> - 🔴 **「再発行」ボタンは押さない。** 押してよいのは、新しく作ったチャネルの「**発行**」だけ
> - **パスワード・2段階認証コードを入力しない**
> - **トークンを扱わない。** チャットに書き出さない・ファイルに保存しない・コミットしない
> - **個人情報をチャットに展開しない。** 台帳を扱うときは件数と列構成だけ報告する
> - 🔴 **最初は1本だけ作る。** 「あれもこれも」と広げない
> - **既存のものを消さない。** `rm -rf` / `mv` を使わない

> 💻 Mac / Windows 共通。コマンドはOSごとに書き分けてあります。

---

## STEP 0｜キットを手に入れる

通常は、利用者から**このページのURL**を渡されて始まります。

1. **Zipが添付されている** → 解凍する
2. **添付が無い** → 下のコマンドで取得する
3. **取得できなかった** → 何度も試さず、利用者に**Zipの添付**を頼む

> 💡 ネットワークが制限されている環境（Codex は既定で無効）では 2 が失敗することがあります。
> 許可を求めるプロンプトが出たら利用者に許可してもらい、通らなければ 3 に切り替えてください。

Mac / Linux
```
cd ~/Desktop && curl -sSL -o line-notify-kit.zip https://ryoya9595.github.io/line-notify-kit/line-notify-kit.zip && unzip -q line-notify-kit.zip
```
Windows（PowerShell）
```
Set-Location "$HOME\Desktop"; Invoke-WebRequest -Uri https://ryoya9595.github.io/line-notify-kit/line-notify-kit.zip -OutFile line-notify-kit.zip; Expand-Archive line-notify-kit.zip -DestinationPath .
```

## STEP 1｜全体像を説明し、確認を取る

> **自分専用のLINE通知**を作ります。毎日きまった時刻にGitHubが自動で動いて、あなたが決めた条件でLINEに通知を送ります。
>
> まず「何を通知するか」を一緒に決めます。白紙で考えなくて大丈夫です。
>
> **Claudeの有料プランは要りません。** 設置したあとはGitHubだけで動き続けます（費用0円）。
> いま配信に使っている公式アカウントには触りません。
>
> お願いするのは、質問への回答・ログイン・トークンの貼り付けだけです。所要は1時間ほどです。

> 「まず、何を通知したいかを決めるところから始めます。よろしいですか？」

## STEP 2｜自分に何ができるか確認する

| 確認 | 方法 |
|---|---|
| **ブラウザ操作** | ブラウザを操作するツールが使えるか（Claude Code なら `mcp__claude-in-chrome__*`。deferred なら先に読み込む） |
| `git` | `git --version` |
| `gh`（GitHub CLI） | `gh auth status` … 使えるとリポジトリ作成・Secrets登録が速い |
| `python3` | `python3 --version`（Windows は `python --version`） |

**ブラウザ操作が使えない場合**（Codex など）：
`事前準備ガイド.md` の該当箇所を**1ステップずつ読み上げて案内**する形に切り替えてください。
**それでも導入は問題なく完了できます。** 時間が10〜20分ほど延びるだけです。

## STEP 3｜何を通知するか決める（ここが最重要）

`何を通知するか決めるシート.md` を開き、**Q1から順に**聞いてください。

> ⚠️ **「何を通知したいですか？」と白紙で聞かない。**
> 「最近、忘れて困ったことはありますか？」から入ります。

型を判定したら、`通知の型カタログ.md` で確認し、利用者に伝えます：

> 「それは『期限の監視』にあたります。一覧を持っておいて、30日前・7日前・当日に知らせる形にできます。これで合っていますか？」

> 🔴 **次の2つに該当したら、このキットでは作らず、専用キットを案内してください。**
>
> - **AIが探して選ぶもの**（案件・情報収集。取得先が決まっていない）
>   → https://ryoya9595.github.io/anken-watch/ （Claude Pro以上が必要）
> - **LINEから登録・操作したいもの**
>   → https://ryoya9595.github.io/tanjobi-line/ （Vercelが必要）
>
> 無理にこのキットで作らないこと。器が違います。

🔴 **作るのは1本だけ。** 複数出てきたら「いちばん困ったのはどれですか？」で絞ります。

## STEP 4｜通知用のLINEを用意する

> 「通知を受け取るLINE公式アカウントを新しく作ります。いま使っているアカウントには触りません。進めてよいですか？」

`事前準備ガイド.md` の STEP 1-1 〜 1-5 の順に進める。要点：

1. https://manager.line.biz/ でアカウント作成。ログインは担当者
2. 応答設定：あいさつメッセージ・応答メッセージを**オフ**
3. 「設定 → Messaging API → Messaging APIを利用する」。**プロバイダーは新規作成**を勧める
4. LINE Developers →「Messaging API設定」→ チャネルアクセストークン（長期）の「**発行**」
   - 🔴 表示が「再発行」なら押さない
   - トークンは**読み上げない・書き出さない**
5. 「チャネル基本設定」→「**あなたのユーザーID**」を控えてもらう
6. QRコードを表示し、スマホで**友だち追加**してもらう
   - ⚠️ **「追加できました」の返事をもらってから次へ**

## STEP 5｜GitHub にリポジトリを作る

> 「毎日動かす場所を用意します。進めてよいですか？」

通知の中身に個人情報が入るなら **Private** で作ります（判断がつかなければ Private）。

**`gh` が使える場合（推奨）**

```
mkdir -p ~/line-notify && cd ~/line-notify
cp -R "<このキットのパス>/base/." .
git init -b main
git add -A && git commit -m "LINE通知キットを追加"
gh repo create line-notify --private --source=. --push
```
（Windows は `Copy-Item -Recurse "<このキットのパス>\base\*" .`）

⚠️ `base/` というフォルダごとではなく、**中身をリポジトリ直下に置く**（`run.py` が直下に来る形）。

確認：`git ls-files` に次が含まれること。

```
run.py
notify.py
state.py
checkers/_template.py
.github/workflows/notify.yml
requirements.txt
AGENTS.md
```

## STEP 6｜Secrets と権限を設定する

**`gh` が使える場合**：担当者にターミナルで直接入力してもらう（チャットに貼らせない）。

```
gh secret set LINE_CHANNEL_ACCESS_TOKEN --repo <owner>/line-notify
gh secret set LINE_TO_USER_ID --repo <owner>/line-notify
```

**ブラウザの場合**：Settings → Secrets and variables → Actions → New repository secret。
Name はあなたが入力し、Value だけ担当者に貼ってもらう。

**あわせて**：Settings → Actions → General → Workflow permissions を
「**Read and write permissions**」にする（`state.json` を書き戻すため）。

## STEP 7｜通知を1本つくる

STEP 3 で決めた内容を、`checkers/` に1ファイル書きます。

1. `checkers/_template.py` をコピーして、分かりやすい名前を付ける（`_` 始まりにしない）
2. `TITLE` と `run(today, state)` を書く
3. 型に応じて、既存の実例を参考にする：

| 型 | 参考にするファイル |
|---|---|
| Lv1 定期リマインド | `checkers/example_weekly_reminder.py` |
| Lv2 記念日・期限 | `checkers/example_deadline.py` |
| Lv3-a 新着チェック | `checkers/example_rss_new.py` |

4. 使わない実例は**削除**する（そのままだと余計な通知が届きます）

> 🔴 **通知することが無いときは必ず `None` を返す。**
> 「今日はありません」という文字列を返すと、毎日それが届いて、そのうち見なくなります。

> 🔴 **新着チェック型を書くときは、`state` の記録を「送信の前」に確定させない。**
> `run.py` は送信が成功したときだけ `state.json` を保存します。この順序を崩すと、
> 送信に失敗した回の分が二度と通知されません。

## STEP 8｜手元で確認する

```
python3 run.py --list                        見つかっているか
python3 run.py --dry-run                     送らずに、届く内容を見る
python3 run.py --dry-run --date 2026-09-22   その日で試す
python3 run.py --only <名前> --dry-run        1本だけ試す
```

**必ず「鳴る日」と「鳴らない日」の両方を試してください。**
毎日鳴ってしまう作りになっていないかの確認です。

土台を触った場合は：

```
python3 dev/test_base.py
```

## STEP 9｜実際に動かす

1. 変更を push する
2. GitHubの「**Actions**」タブ →「**LINE通知**」→「**Run workflow**」
   - `dry_run` にチェックを入れると、送らずにログだけ確認できます
3. まず `dry_run` で1回、次に本番で1回
4. LINEに届いたか担当者に確認してもらう

| 症状 | 見るところ |
|---|---|
| 401 | Secrets のトークン |
| 400 | ユーザーID、または**友だち追加していない** |
| 何も届かない | ログに「何も送りません」と出ていれば正常（通知することが無かった） |
| state.json のpushで失敗 | Settings → Actions → Workflow permissions |

## STEP 10｜cron を設定する

`.github/workflows/notify.yml` の `cron` を、STEP 3 で決めた時刻に変えます（**UTC**。日本時間 −9時間）。

| 日本時間 | cron |
|---|---|
| 朝7時 | `0 22 * * *` |
| 朝8時 | `0 23 * * *` |
| 朝9時 | `0 0 * * *` |
| 平日の朝8時 | `0 23 * * 0-4` |

> ⚠️ 曜日もUTCでずれます。日本の月〜金は、UTCでは日〜木（`0-4`）です。
> ⚠️ 実行は混雑時に数十分ずれます。きっかりには来ません。

## STEP 11｜完了を伝える

> 「導入できました。毎朝○時ごろに届きます。通知することが無い日は、何も届きません。
>
> **まずはこの1本を1週間使ってみてください。**
> ・多すぎる → 減らす方向に調整します
> ・欲しいものが足りない → もう1本足します
>
> 通知を増やしたくなったら、私に『通知を1つ増やしたい』と言ってください。
> `checkers/` にファイルを1つ足すだけで増やせます。届くのは1通のままです。」

---

## 通知を1つ増やしてと言われたら

1. `何を通知するか決めるシート.md` で、何を作るか決める
2. `checkers/_template.py` をコピーして書く
3. `python3 run.py --only <名前> --dry-run` で確認
4. push する

**登録作業は要りません。** `checkers/` に置けば `run.py` が自動で見つけます。

## コードを直したとき

```
python3 dev/test_base.py
```

チェッカーの読み込み（`_` 始まりを無視するか）、例外が出ても他が動くか、
`None` を返したものが通知に入らないか、通知済みの記録、設定の検証を確認します。
ネットにもLINEにも接続しません。
