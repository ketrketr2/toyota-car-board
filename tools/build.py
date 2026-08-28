#!/usr/bin/env python3
"""①車種別AI分析ボード: パーツ結合 → plain.html"""
import json, os
CB = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.environ.get('BOARD_DATA', 'board_data.json')))
head = open(f'{CB}/part_head.html', encoding='utf-8').read()
js = '\n'.join(open(f'{CB}/part_js{i}.js', encoding='utf-8').read() for i in (1, 2, 3))
html = head + '\n<script>\nwindow.DATA=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n</script>\n<script>\n' + js + '\n</script>\n</body>\n</html>\n'
open('plain.html', 'w', encoding='utf-8').write(html)
print(f'plain.html {len(html.encode())/1024:.0f}KB')
