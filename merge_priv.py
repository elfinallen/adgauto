#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并 AdGuard Tracking Filter 和 EasyPrivacy
仅保留路径级规则 (||domain/path^)
"""

import requests
import re
from datetime import datetime

SOURCES = [
    "https://filters.adtidy.org/android/filters/3_optimized.txt",
    "https://easylist.to/easylist/easyprivacy.txt"
]

OUTPUT_FILE = "adgprv.txt"

def fetch(url):
    try:
        print(f"📥 下载：{url}")
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"❌ 下载失败 {url}: {e}")
        return ""

def parse_path_rules(content):
    """仅保留路径级规则 (必须包含路径 /)"""
    rules = set()
    pattern = re.compile(r'^\|\|(.+)\^(\$?.*)?$')
    
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('!') or line.startswith('#') or line.startswith('['):
            continue
        if not line.startswith('||'):
            continue
        
        match = pattern.match(line)
        if match:
            url_part = match.group(1)
            # 路径级规则：必须包含 /
            if '/' in url_part:
                options = match.group(2) if match.group(2) else ""
                rules.add(f"||{url_part}^{options}")
    
    return rules

def main():
    all_rules = set()
    
    for url in SOURCES:
        content = fetch(url)
        if content:
            rules = parse_path_rules(content)
            print(f"✅ 提取 {len(rules)} 条路径规则")
            all_rules.update(rules)
    
    sorted_rules = sorted(all_rules)
    
    header = [
        "! Title: AdGuard Privacy",
        "! Description: composed of other filters (AdGuard Tracking & EasyPrivacy)",
        f"! Count: {len(sorted_rules)}",
        f"! Updated: {datetime.now().isoformat()}",
        "! Expires: 3 days",
        ""
    ]
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(header) + "\n".join(sorted_rules) + "\n")
    
    print(f"📄 生成 {OUTPUT_FILE} 共 {len(sorted_rules)} 条规则")

if __name__ == "__main__":
    main()