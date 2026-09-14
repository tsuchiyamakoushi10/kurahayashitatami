#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GA4 の計測タグと Search Console の確認用メタタグを全ページに挿入する。
何度実行しても重複しない（既存の同じブロックを入れ替える）。

  ./tools/set-analytics.py --ga4 G-XXXXXXXXXX
  ./tools/set-analytics.py --verify xxxxxxxxxxxxxxxxxxxxxxxx
  ./tools/set-analytics.py --ga4 G-XXXXXXXXXX --verify xxxxxxxxxxxxxxxxxxxxxxxx

タグを外したいときは --remove を付ける。
"""
import argparse, pathlib, re

# 計測を入れるファイル（リポジトリ直下からの相対パス）
PAGES = [
    'src/pages/top.html',
    'src/pages/products.html',
    'src/pages/works.html',
    'src/pages/tatami.html',
    'src/pages/company-story.html',
    'src/pages/privacy.html',
    '404.html',          # リンク切れがどれだけ起きているかを知るため
]

BEGIN, END = '<!-- 計測タグ ここから -->', '<!-- 計測タグ ここまで -->'

# 問い合わせ導線が電話だけなので、電話ボタンのタップが実質のコンバージョン。
# GA4の拡張計測では tel: のタップは取れないので自前で送る。
TEL_TRACKING = """    // 電話ボタンのタップを計測する。設置場所も一緒に送るので、
    // ヘッダー・最終CTA・フッターのどれが押されているかが分かる。
    document.addEventListener('click', function (e) {
      var a = e.target && e.target.closest && e.target.closest('a[href^="tel:"]');
      if (!a) return;
      gtag('event', 'tel_tap', {
        tel_location: a.dataset.telLocation
                    || (a.closest('.site-header') ? 'header'
                     :  a.closest('.final-cta')   ? 'cta'
                     :  a.closest('footer')       ? 'footer'
                     :  a.closest('table')        ? 'company_info'
                     :  'other'),
        link_url: a.getAttribute('href'),
        page_path: location.pathname
      });
    }, true);"""


def build(ga4, verify):
    lines = ['  ' + BEGIN]
    if verify:
        lines.append(f'  <meta name="google-site-verification" content="{verify}">')
    if ga4:
        lines += [
            f'  <script async src="https://www.googletagmanager.com/gtag/js?id={ga4}"></script>',
            '  <script>',
            '    window.dataLayer = window.dataLayer || [];',
            '    function gtag(){dataLayer.push(arguments);}',
            "    gtag('js', new Date());",
            f"    gtag('config', '{ga4}');",
            '',
            TEL_TRACKING,
            '  </script>',
        ]
    lines.append('  ' + END)
    return '\n' + '\n'.join(lines) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ga4', help='GA4 の測定ID (G- で始まる)')
    ap.add_argument('--verify', help='Search Console の google-site-verification の値')
    ap.add_argument('--remove', action='store_true', help='挿入済みの計測タグを取り除く')
    a = ap.parse_args()

    if not a.remove and not (a.ga4 or a.verify):
        ap.error('--ga4 か --verify のどちらかを指定してください（外す場合は --remove）')
    if a.ga4 and not a.ga4.startswith('G-'):
        ap.error(f'GA4の測定IDは G- で始まります (指定値: {a.ga4})')

    root = pathlib.Path(__file__).resolve().parent.parent
    block = '' if a.remove else build(a.ga4, a.verify)
    pat = re.compile(r'\n[ \t]*' + re.escape(BEGIN) + r'.*?' + re.escape(END) + r'[ \t]*\n', re.S)

    for rel in PAGES:
        p = root / rel
        s = p.read_text(encoding='utf-8')

        # 既存ブロックがあれば入れ替え、無ければ </head> の直前に入れる
        if pat.search(s):
            s = pat.sub(block if block else '\n', s)
        elif block:
            s = s.replace('</head>', block.rstrip('\n') + '\n</head>', 1)

        p.write_text(s, encoding='utf-8')
        print(f'  {"削除" if a.remove else "挿入"}: {rel}')

    print('\n完了。git diff で確認してからコミットしてください。')


if __name__ == '__main__':
    main()
