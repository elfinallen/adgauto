import os
import re
import datetime
import requests
import subprocess
from urllib.parse import urlparse

# 配置区域
SOURCES = {
    "dns": [
        "https://filters.adtidy.org/android/filters/15_optimized.txt",
        "https://filters.adtidy.org/android/filters/224_optimized.txt"
    ],
    "ads": [
        "https://filters.adtidy.org/android/filters/2_optimized.txt",
        "https://filters.adtidy.org/android/filters/224_optimized.txt"
    ]
}

OUTPUT_FILES = {
    "dns": "adgdns.txt",
    "ads": "adgads.txt"
}

HEADERS = {
    "dns": [
        "! Title: AdGuard Domain",
        "! Last Modified: " + datetime.datetime.utcnow().isoformat() + "Z",
        ""
    ],
    "ads": [
        "! Title: AdGuard Advert",
        "! Last Modified: " + datetime.datetime.utcnow().isoformat() + "Z",
        ""
    ]
}

# 正则规则
# DNS 规则：以 || 开头，以 ^ 结尾，中间不包含 / (纯域名规则)
REGEX_DNS = re.compile(r'^\|\|[^/]+\^$')
# 正则规则特征：包含 /.../ 结构
REGEX_REGEX_RULE = re.compile(r'/.*?/')

def fetch_url(url):
    try:
        print(f"Fetching: {url}")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text.splitlines()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def filter_dns_rules(lines):
    """仅保留 ||domain^ 规则"""
    filtered = set()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('!') or line.startswith('#') or line.startswith('@'):
            continue
        if REGEX_DNS.match(line):
            filtered.add(line)
    return filtered

def filter_ads_rules(lines):
    """去除正则和纯域名规则，保留 URL 匹配规则"""
    filtered = set()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('!') or line.startswith('#') or line.startswith('@'):
            continue
        # 排除纯域名规则 (||domain^)
        if REGEX_DNS.match(line):
            continue
        # 排除正则规则 (包含 /.../)
        if REGEX_REGEX_RULE.search(line):
            continue
        # 保留其他 (通常是包含路径的 URL 拦截)
        filtered.add(line)
    return filtered

def write_file(filename, header_lines, rules):
    sorted_rules = sorted(list(rules))
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(header_lines) + '\n')
        f.write('\n'.join(sorted_rules) + '\n')
    print(f"Generated {filename} with {len(sorted_rules)} rules.")

def run_git_command():
    """执行 Git 提交和推送"""
    commands = [
        ["git", "config", "--local", "user.email", "github-actions[bot]@users.noreply.github.com"],
        ["git", "config", "--local", "user.name", "github-actions[bot]"],
        ["git", "add", "adgdns.txt", "adgads.txt"],
        ["git", "commit", "-m", "chore: auto update ad rules " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M")],
        ["git", "push"]
    ]
    
    # 检查是否有变更
    diff_proc = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
    if diff_proc.returncode == 0:
        # 如果 diff 返回 0，说明暂存区没有变化（或者 add 后没变化），需要检查工作区是否有变化
        # 更简单的逻辑：直接 add，如果 commit 失败则说明无变化
        pass

    for cmd in commands:
        try:
            # commit 和 push 可能会因为无变化或网络问题失败
            if cmd[1] == "commit":
                # 先检查是否有变化
                status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
                if not status.stdout.strip():
                    print("No changes to commit.")
                    return
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                if cmd[1] == "commit" and "nothing to commit" in result.stderr:
                    print("No changes to commit.")
                    return
                print(f"Command failed: {' '.join(cmd)}")
                print(result.stderr)
                # 非致命错误继续，但 push 失败应停止
                if cmd[1] == "push":
                    raise Exception("Git push failed")
            else:
                print(f"Success: {' '.join(cmd)}")
        except Exception as e:
            print(f"Git error: {e}")
            if cmd[1] == "push":
                raise

def main():
    # 1. 处理 DNS 规则
    print("--- Processing DNS Rules ---")
    dns_rules = set()
    for url in SOURCES["dns"]:
        lines = fetch_url(url)
        dns_rules.update(filter_dns_rules(lines))
    write_file(OUTPUT_FILES["dns"], HEADERS["dns"], dns_rules)

    # 2. 处理 广告拦截规则
    print("--- Processing Ads Rules ---")
    ads_rules = set()
    for url in SOURCES["ads"]:
        lines = fetch_url(url)
        ads_rules.update(filter_ads_rules(lines))
    write_file(OUTPUT_FILES["ads"], HEADERS["ads"], ads_rules)

    # 3. Git 操作
    print("--- Git Operations ---")
    run_git_command()
    print("--- Finished ---")

if __name__ == "__main__":
    main()