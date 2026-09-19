#!/bin/bash
# 配布用Zipを作り直す。
#
# ⚠️ zip コマンドは使わない。macOS の zip は日本語ファイル名に UTF-8 フラグを立てないため、
#    Windows のエクスプローラーで解凍すると文字化けする。Python の zipfile なら自動で立つ。
set -euo pipefail
cd "$(dirname "$0")/.."

echo "▶ 検証"
python3 base/dev/test_base.py > /dev/null 2>&1 || { echo "❌ テストが通らないのでZipを作りません"; exit 1; }
echo "  OK"

python3 - << 'PY'
import os, zipfile

NAME = 'line-notify-kit'
OUT = f'{NAME}.zip'

DOCS = [
    'はじめにお読みください.md',
    '通知の型カタログ.md',
    '何を通知するか決めるシート.md',
    '事前準備ガイド.md',
    '導入手順_AIに読ませる.md',
    '導入をサポートする人へ.md',
]
TREES = ['base']
SKIP_DIRS = {'__pycache__', '.git'}
SKIP_FILES = {'.DS_Store', 'state.json'}

files = list(DOCS)
for tree in TREES:
    for root, dirs, names in os.walk(tree):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for n in sorted(names):
            if n not in SKIP_FILES:
                files.append(os.path.join(root, n))

missing = [f for f in files if not os.path.exists(f)]
if missing:
    raise SystemExit('❌ 見つからないファイル: ' + ', '.join(missing))

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in files:
        # base/ の中身はリポジトリ直下に置く想定なので、階層を保ったまま入れる
        z.write(f, f'{NAME}/{f}')

with zipfile.ZipFile(OUT) as z:
    bad = [i.filename for i in z.infolist()
           if not i.filename.isascii() and not (i.flag_bits & 0x800)]
    if bad:
        raise SystemExit('❌ UTF-8フラグが立っていません: ' + ', '.join(bad))
    print(f'\n✅ {OUT}  （{len(z.infolist())}ファイル / {os.path.getsize(OUT):,} バイト）')
    for i in z.infolist():
        print(f'   {i.file_size:>7,}  {i.filename}')
PY
