#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并 AdGuard Annoyance & Social Filter
仅保留路径级规则 (||domain/path^)
"""

import requests
import re
from datetime import datetime
import sys

SOURCES = [
    "https://filters.adtidy.org/android/filters/4_optimized.txt",
    "https://filters.adtidy.org/android/filters/14_optimized.txt"
]

OUTPUT_FILE = "adgany.txt"

def fetch(url):
    try:
        print(f"📥 下载：{url}")
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"⚠️ 下载失败 {url}: {e}")
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
            if '/' in url_part:
                options = match.group(2) if match.group(2) else ""
                rules.add(f"||{url_part}^{options}")
    
    return rules

def main():
    try:
        all_rules = set()
        
        for url in SOURCES:
            content = fetch(url)
            if content:
                rules = parse_path_rules(content)
                print(f"✅ 提取 {len(rules)} 条路径规则")
                all_rules.update(rules)
        
        if not all_rules:
            print("⚠️ 警告：未提取到任何规则，但继续生成空文件")
        
        sorted_rules = sorted(all_rules)
        
        header = [
        "! Title: AdGuard Annoy",
        "! Description: composed of other filters (AdGuard Annoyance & Social Filter)",
        f"! Count: {len(sorted_rules)}",
        f"! Updated: {datetime.now().isoformat()}",
        "! Expires: 3 days",
            ""
        ]
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(header) + "\n".join(sorted_rules) + "\n")
        
        print(f"📄 生成 {OUTPUT_FILE} 共 {len(sorted_rules)} 条规则")
        return 0
        
    except Exception as e:
        print(f"❌ 脚本执行错误：{e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())