#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SIGNAL ROOM: テンプレ + signal_data.json + carimg.json → signal_plain.html"""
import json, os
CB = os.path.dirname(os.path.abspath(__file__))
data = open(os.environ.get("SIGNAL_DATA", "signal_data.json"), encoding="utf-8").read().replace("<", "\\u003c")
img = open(f"{CB}/carimg.json", encoding="utf-8").read()
tpl = open(f"{CB}/signal_template.html", encoding="utf-8").read()
tpl = tpl.replace("const DATA = __DATA__;", "const DATA = " + data + ";", 1)
tpl = tpl.replace("const IMG = __IMG__;", "const IMG = " + img + ";", 1)
i = tpl.index("<header")
FAVICON = "<link rel=\"icon\" href=\"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='24' fill='%23060709'/><circle cx='50' cy='54' r='30' fill='none' stroke='%236C9EFF' stroke-width='9'/><circle cx='50' cy='54' r='8' fill='%236C9EFF'/><path d='M20 30 Q50 6 80 30' fill='none' stroke='%236C9EFF' stroke-width='8' stroke-linecap='round'/></svg>\">"
html = ("<!DOCTYPE html>\n<!--CARAI_BOARD-->\n<html lang=\"ja\"><head><meta charset=\"UTF-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<meta name=\"robots\" content=\"noindex,nofollow\">" + FAVICON + "\n"
        + tpl[:i] + "</head><body>\n" + tpl[i:] + "\n</body></html>\n")
open("signal_plain.html", "w", encoding="utf-8").write(html)
print(f"signal_plain.html {len(html.encode())//1024}KB")
