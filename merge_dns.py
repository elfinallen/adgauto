#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并 AdGuard DNS Filter, AdGuard Chinese Filter
仅保留域名级规则 (||domain^)
"""

import requests
import re
from datetime import datetime

SOURCES = [
    "https://filters.adtidy.org/android/filters/15_optimized.txt",
    "https://filters.adtidy.org/android/filters/224_optimized.txt"
]

OUTPUT_FILE = "adgdns.txt"

def fetch(url):
    try:
        print(f"📥 下载：{url}")
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"❌ 下载失败 {url}: {e}")
        return ""

def parse_domain_rules(content):
    """仅保留域名级规则 (不包含路径 /)"""
    rules = set()
    pattern = re.compile(r'^\|\|([a-zA-Z0-9\.\-\*]+)\^(\$?.*)?$')
    
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('!') or line.startswith('#') or line.startswith('['):
            continue
        if not line.startswith('||'):
            continue
        
        match = pattern.match(line)
        if match:
            domain_part = match.group(1)
            # 域名级规则：不能包含 /
            if '/' not in domain_part:
                options = match.group(2) if match.group(2) else ""
                rules.add(f"||{domain_part}^{options}")
    
    return rules

def main():
    all_rules = set()
    
    for url in SOURCES:
        content = fetch(url)
        if content:
            rules = parse_domain_rules(content)
            print(f"✅ 提取 {len(rules)} 条域名规则")
            all_rules.update(rules)
    
    # 排序并写入
    sorted_rules = sorted(all_rules)
    
    header = [
        "! Title: AdGuard Domain",
        "! Description: composed of other filters (AdGuard DNS & Chinese Filter)",
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