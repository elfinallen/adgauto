import os
import re
import requests
import subprocess
from datetime import datetime

# 配置部分
SOURCES = {
    "dns": [
        "https://filters.adtidy.org/android/filters/15_optimized.txt",
        "https://filters.adtidy.org/android/filters/224_optimized.txt"
    ],
    "ads": [
        "https://filters.adtidy.org/android/filters/2_optimized.txt",
        "https://filters.adtidy.org/android/filters/224_optimized.txt"
    ],
    "prv": [
        "https://filters.adtidy.org/android/filters/3_optimized.txt",
        "https://filters.adtidy.org/android/filters/118_optimized.txt"
    ]
}

OUTPUT_FILES = {
    "dns_full": "adgdns_full.txt",
    "ads_full": "adgads_full.txt",
    "prv_full": "adgprv_full.txt",
    "dns": "adgdns.txt",
    "ads": "adgads.txt",
    "prv": "adgprv.txt"
}

HEADERS = {
    "dns_full": [
        "! Title: AdGuard Domain",
        "! Description: DNS Filter composed of other filters (AdGuard DNS & Chinese Filter)",
        "! Homepage: https://github.com/elfinallen/adgauto"
    ],
    "ads_full": [
        "! Title: AdGuard Advert",
        "! Description: ADS Filter composed of other filters (AdGuard Base & Chinese Filter)",
        "! Homepage: https://github.com/elfinallen/adgauto"
    ],
    "prv_full": [
        "! Title: AdGuard Privacy",
        "! Description: Privacy Filter composed of other filters (AdGuard tracking & EasyPrivacy)",
        "! Homepage: https://github.com/elfinallen/adgauto"
    ],
    "dns": [
        "! Title: AdGuard Domain Lite",
        "! Description: DNS Filter composed of other filters (AdGuard DNS & Chinese Filter), removed uncommon rules",
        "! Homepage: https://github.com/elfinallen/adgauto"
    ],
    "ads": [
        "! Title: AdGuard Advert Lite",
        "! Description: ADS Filter composed of other filters (AdGuard Base & Chinese Filter), removed uncommon rules",
        "! Homepage: https://github.com/elfinallen/adgauto"
    ],
    "prv": [
        "! Title: AdGuard Privacy Lite",
        "! Description: Privacy Filter composed of other filters (AdGuard tracking & EasyPrivacy), removed uncommon rules",
        "! Homepage: https://github.com/elfinallen/adgauto"
    ]
}

# 正则规则
# 注释和白名单
RE_CMT = re.compile(r'^!|^#|\@|^\[')
# 纯域名规则 (||domain^)，中间不含 /
RE_DNS = re.compile(r'^\|\|[^/]+\^$')
# 纯数字 IP 规则 (||123.456.789.012^)
RE_IP = re.compile(r'^\|\|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\^$')
# URL 规则
RE_URL1 = re.compile(r'^\$|^\*|^%')
# third-party 规则
RE_3P = re.compile(r'\$third-party', re.IGNORECASE)
# CSS 和 $$ 规则
RE_CSS = re.compile(r'#|\$\$')

def fetch_content(url):
    try:
        print(f"Fetching: {url}")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text.splitlines()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def filter_rules(lines, rule_type):
    filtered = set()
    for line in lines:
        line = line.strip()
        if not line or RE_CMT.match(line):
            continue
        
        # 转小写合并去重
        line_lower = line.lower()

        if rule_type == "dns_full":
            # 只保留纯域名规则 ||domain^
            if RE_DNS.match(line):
                filtered.add(line_lower)
        
        elif rule_type == "dns":
            if RE_DNS.match(line):
                # 去除纯IP规则
                if not RE_IP.match(line):
                    filtered.add(line_lower)
        
        elif rule_type in ["ads_full", "prv_full"]:
            # 去除 CSS 和纯域名规则
            if RE_CSS.search(line) or RE_DNS.match(line):
                continue
            # 保留其他规则
            filtered.add(line_lower)
        
        elif rule_type in ["ads", "prv"]:
            # 去除 CSS 和纯域名规则
            if RE_CSS.search(line) or RE_DNS.match(line):
                continue
            # 去除 $third-party 规则
            if RE_3P.search(line):
                continue
            # 保留其他规则
            filtered.add(line_lower)
    
    return sorted(list(filtered))

def write_file(filename, header_lines, rules):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(filename, "w", encoding="utf-8") as f:
        for h in header_lines:
            f.write(f"{h}\n")
        f.write(f"! Last Updated: {timestamp}\n")
        f.write(f"! Total Rules: {len(rules)}\n")
        f.write(f"! Expires: 5 days\n")
        for rule in rules:
            f.write(f"{rule}\n")

def git_commit_push():
    subprocess.run(["git", "config", "--local", "user.email", "github-actions[bot]@users.noreply.github.com"])
    subprocess.run(["git", "config", "--local", "user.name", "github-actions[bot]"])
    
    # 检查是否有变更
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not status.stdout.strip():
        print("No changes to commit.")
        return

    # 添加、提交、推送
    subprocess.run(["git", "add", "."])
    commit_msg = f"auto update {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    subprocess.run(["git", "commit", "-m", commit_msg])
    subprocess.run(["git", "push"])

def main():
    all_rules = {}
    
    # 处理每一类规则
    for category, urls in SOURCES.items():
        print(f"Processing category: {category}")
        merged_lines = []
        for url in urls:
            merged_lines.extend(fetch_content(url))
        
        # 标准版本
        full_category = f"{category}_full"
        filtered_full_rules = filter_rules(merged_lines, full_category)
        all_rules[full_category] = filtered_full_rules
        
        # 精简版本
        filtered_rules = filter_rules(merged_lines, category)
        all_rules[category] = filtered_rules

    # 写入文件
    for category, rules in all_rules.items():
        filename = OUTPUT_FILES[category]
        header = HEADERS[category]
        write_file(filename, header, rules)

    # 自动提交
    git_commit_push()

if __name__ == "__main__":
    main()