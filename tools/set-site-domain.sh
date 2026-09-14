#!/usr/bin/env bash
# サイトの正規URLを一括で差し替える。何度でも実行できる。
#
#   ./tools/set-site-domain.sh https://www.kurahayashi-tatami.com
#
# 現在の値は src/pages/top.html の canonical から自動で読み取る。
# 末尾のスラッシュは付けないこと。実行後 git diff で確認してからコミットする。
set -euo pipefail

NEW="${1:-}"
if [[ -z "$NEW" ]]; then
  echo "使い方: $0 https://example.com" >&2
  exit 1
fi
if [[ "$NEW" != https://* ]]; then
  echo "エラー: https:// で始まるURLを指定してください (指定値: $NEW)" >&2
  exit 1
fi
if [[ "$NEW" == */ ]]; then
  echo "エラー: 末尾のスラッシュは外してください (指定値: $NEW)" >&2
  exit 1
fi

cd "$(dirname "$0")/.."

# 現在の正規URL（初回は仮置きの SITE-DOMAIN-TBD）
OLD=$(sed -n 's#.*<link rel="canonical" href="\(https://[^/"]*\)/*".*#\1#p' src/pages/top.html | head -1)
if [[ -z "$OLD" ]]; then
  echo "エラー: src/pages/top.html から現在のドメインを読み取れませんでした" >&2
  exit 1
fi
if [[ "$OLD" == "$NEW" ]]; then
  echo "すでに $NEW です。変更はありません。"
  exit 0
fi

echo "  $OLD"
echo "    ↓"
echo "  $NEW"
echo

grep -rl "$OLD" --exclude-dir=.git --exclude-dir=tools . | while read -r f; do
  sed -i "s#$OLD#$NEW#g" "$f"
  echo "  差し替え: $f"
done

echo
echo "完了。git diff で確認してからコミットしてください。"
