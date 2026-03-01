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
    "privacy": [
        "https://filters.adtidy.org/android/filters/3_optimized.txt",
        "https://filters.adtidy.org/android/filters/118_optimized.txt"
    ]
}

OUTPUT_FILES = {
    "dns": "adgdns.txt",
    "ads": "adgads.txt",
    "privacy": "adgprv.txt"
}

HEADERS = {
    "dns": [
        "! Title: AdGuard Domain",
        "! Description: DNS Filter composed of other filters (AdGuard DNS & Chinese Filter)"
    ],
    "ads": [
        "! Title: AdGuard Advert",
        "! Description: ADS Filter composed of other filters (AdGuard Base & Chinese Filter)"
    ],
    "privacy": [
        "! Title: AdGuard Privacy",
        "! Description: Privacy Filter composed of other filters (AdGuard tracking & EasyPrivacy)"
    ]
}

# 正则规则
# 注释行
RE_CMT = re.compile(r'^!|^#|^\[')
# CSS 规则
RE_CSS = re.compile(r'#')
# 纯域名规则 (||domain^)，中间不包含 /
RE_DOMAIN_ONLY = re.compile(r'^\|\|[^/]+\^$')
# 通用网络规则 (以 || 或 | 开头)
RE_NETWORK = re.compile(r'^\|\||^\|')

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
        
        # 转小写进行去重
        line_lower = line.lower()

        if rule_type == "dns":
            # 只保留纯域名规则 ||domain^
            if RE_DOMAIN_ONLY.match(line):
                filtered.add(line_lower)
        
        elif rule_type in ["ads", "privacy"]:
            # 去除 CSS 规则
            if RE_CSS.search(line):
                continue
            # 去除纯域名规则
            if RE_DOMAIN_ONLY.match(line):
                continue
            # 保留其余规则
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
    print(f"Written {len(rules)} rules to {filename}")

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
    commit_msg = f"chore: auto update rules {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    subprocess.run(["git", "commit", "-m", commit_msg])
    subprocess.run(["git", "push"])
    print("Git push successful.")

def main():
    all_rules = {}
    
    # 处理每一类规则
    for category, urls in SOURCES.items():
        print(f"Processing category: {category}")
        merged_lines = []
        for url in urls:
            merged_lines.extend(fetch_content(url))
        
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