#!/usr/bin/env python3
"""Generate index.html listing all complex trauma daily reports."""

import glob
import os
from datetime import datetime

html_files = sorted(glob.glob("docs/complex-trauma-*.html"), reverse=True)
links = ""
for f in html_files[:60]:
    name = os.path.basename(f)
    date = name.replace("complex-trauma-", "").replace(".html", "")
    try:
        d = datetime.strptime(date, "%Y-%m-%d")
        date_display = d.strftime("%Y年%-m月%-d日")
    except Exception:
        date_display = date
    weekday_names = ["一", "二", "三", "四", "五", "六", "日"]
    weekday = ""
    if len(date) == 10:
        try:
            weekday = weekday_names[datetime.strptime(date, "%Y-%m-%d").weekday()]
        except Exception:
            pass
    links += f'<li><a href="{name}">\U0001f4c5 {date_display}（週{weekday}）</a></li>\n'

total = len(html_files)

index = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Complex Trauma Brain \u00b7 心理創傷文獻日報</title>
<style>
  :root {{ --bg: #f0f4f3; --surface: #f8faf9; --line: #c8d5d0; --text: #1a2e28; --muted: #5a7568; --accent: #2d6a4f; --accent-soft: #d8ede3; }}
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: radial-gradient(ellipse at top left, #e8f0ec 0, var(--bg) 40%, #dce5e0 100%); color: var(--text); font-family: "Noto Sans TC", "PingFang TC", "Helvetica Neue", Arial, sans-serif; min-height: 100vh; }}
  .container {{ position: relative; z-index: 1; max-width: 640px; margin: 0 auto; padding: 80px 24px; }}
  .logo {{ font-size: 48px; text-align: center; margin-bottom: 16px; }}
  h1 {{ text-align: center; font-size: 24px; color: var(--text); margin-bottom: 8px; }}
  .subtitle {{ text-align: center; color: var(--accent); font-size: 14px; margin-bottom: 8px; }}
  .description {{ text-align: center; color: var(--muted); font-size: 13px; margin-bottom: 48px; line-height: 1.6; }}
  .count {{ text-align: center; color: var(--muted); font-size: 13px; margin-bottom: 32px; }}
  ul {{ list-style: none; }}
  li {{ margin-bottom: 8px; }}
  a {{ color: var(--text); text-decoration: none; display: block; padding: 14px 20px; background: var(--surface); border: 1px solid var(--line); border-radius: 12px; transition: all 0.2s; font-size: 15px; }}
  a:hover {{ background: var(--accent-soft); border-color: var(--accent); transform: translateX(4px); }}
  .clinic-links {{ margin-top: 40px; display: flex; flex-direction: column; gap: 10px; }}
  .clinic-link {{ display: flex; align-items: center; gap: 12px; padding: 16px 20px; background: var(--surface); border: 1px solid var(--line); border-radius: 12px; text-decoration: none; color: var(--text); transition: all 0.2s; }}
  .clinic-link:hover {{ background: var(--accent-soft); border-color: var(--accent); }}
  .clinic-icon {{ font-size: 24px; }}
  .clinic-info {{ flex: 1; }}
  .clinic-name {{ font-size: 14px; font-weight: 600; }}
  .clinic-desc {{ font-size: 11px; color: var(--muted); margin-top: 2px; }}
  footer {{ margin-top: 40px; text-align: center; font-size: 12px; color: var(--muted); }}
  footer a {{ display: inline; padding: 0; background: none; border: none; color: var(--muted); }}
  footer a:hover {{ color: var(--accent); }}
</style>
</head>
<body>
<div class="container">
  <div class="logo">\U0001f9e0</div>
  <h1>Complex Trauma Brain</h1>
  <p class="subtitle">心理創傷、複雜性創傷與解離領域文獻日報</p>
  <p class="description">每日自動從 PubMed 彙整最新心理創傷、CPTSD、解離、<br/>童年創傷相關研究，由 AI 分析整理</p>
  <p class="count">共 {total} 份報告</p>
  <ul>{links}</ul>
  <div class="clinic-links">
    <a href="https://www.leepsyclinic.com/" class="clinic-link" target="_blank">
      <span class="clinic-icon">\U0001f3e5</span>
      <div class="clinic-info">
        <div class="clinic-name">李政洋身心診所首頁</div>
        <div class="clinic-desc">專業身心科門診服務</div>
      </div>
    </a>
    <a href="https://blog.leepsyclinic.com/" class="clinic-link" target="_blank">
      <span class="clinic-icon">\U0001f4e8</span>
      <div class="clinic-info">
        <div class="clinic-name">訂閱電子報</div>
        <div class="clinic-desc">定期接收最新心理健康資訊</div>
      </div>
    </a>
  </div>
  <footer>
    <p>Powered by PubMed + Zhipu AI \u00b7 <a href="https://github.com/u8901006/complex-trauma-brain">GitHub</a></p>
  </footer>
</div>
</body>
</html>"""

with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(index)
print("Index page generated")
