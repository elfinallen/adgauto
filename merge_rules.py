import requests
import re
import datetime
import os
import subprocess

# 配置规则源 URL
URLS = {
    "dns": "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt",
    "base": "https://raw.githubusercontent.com/AdguardTeam/AdGuardFilters/master/BaseFilter/sections/adservers.txt",
    "chinese": "https://raw.githubusercontent.com/AdguardTeam/AdGuardFilters/master/ChineseFilter/sections/adservers.txt"
}

# 输出文件
OUTPUT_DNS = "adgdns.txt"
OUTPUT_ADS = "adgads.txt"

def fetch_content(url):
    """获取远程文件内容"""
    try:
        print(f"Fetching: {url}")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def parse_rules(content):
    """解析规则，去除注释和空行"""
    rules = []
    for line in content.splitlines():
        line = line.strip()
        # 跳过空行、注释 (!)、元数据 ([])
        if not line or line.startswith('!') or line.startswith('['):
            continue
        rules.append(line)
    return rules

def is_domain_rule(rule):
    """
    判断是否为域名级规则 (适合 DNS 过滤)
    特征：以 || 开头，以 ^ 结尾，中间不包含 / (路径)
    允许包含 $ 修饰符 (如 $important)，但不允许包含 /
    """
    if not rule.startswith('||'):
        return False
    # 提取 || 和 ^ 之间的部分
    match = re.match(r'^\|\|([^$^]+)\^', rule)
    if not match:
        return False
    domain_part = match.group(1)
    # 如果域名部分包含 /，则是路径规则
    if '/' in domain_part:
        return False
    return True

def process_rules():
    # 1. 拉取数据
    dns_content = fetch_content(URLS["dns"])
    base_content = fetch_content(URLS["base"])
    chinese_content = fetch_content(URLS["chinese"])

    # 2. 解析
    dns_rules = set(parse_rules(dns_content))
    base_rules = set(parse_rules(base_content))
    chinese_rules = set(parse_rules(chinese_content))

    # 3. 分类处理
    # adgdns.txt: DNS 源 + 中文源 -> 仅保留域名级
    dns_candidates = dns_rules.union(chinese_rules)
    final_dns = {r for r in dns_candidates if is_domain_rule(r)}

    # adgads.txt: Base 源 + 中文源 -> 仅保留路径级 (非域名级)
    ads_candidates = base_rules.union(chinese_rules)
    # 路径级定义为：在候选集中，且不是域名级规则
    final_ads = {r for r in ads_candidates if not is_domain_rule(r)}

    # 4. 排序 (为了 diff 友好)
    sorted_dns = sorted(list(final_dns))
    sorted_ads = sorted(list(final_ads))

    # 5. 生成文件头
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    header = f"! Updated: {now}\n! Source: AdGuard DNS + Base + Chinese Filter\n\n"

    # 6. 写入文件
    def write_file(filename, rules):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(header)
            f.write("\n".join(rules))
            f.write("\n")
        print(f"Generated {filename} with {len(rules)} rules.")

    write_file(OUTPUT_DNS, sorted_dns)
    write_file(OUTPUT_ADS, sorted_ads)

def git_commit_push():
    """检查变更并提交推送"""
    # 配置 Git 用户
    subprocess.run(["git", "config", "--local", "user.name", "github-actions[bot]"])
    subprocess.run(["git", "config", "--local", "user.email", "github-actions[bot]@users.noreply.github.com"])
    
    # 添加文件
    subprocess.run(["git", "add", OUTPUT_DNS, OUTPUT_ADS])
    
    # 检查是否有变更
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not result.stdout.strip():
        print("No changes to commit.")
        return

    # 提交
    commit_msg = f"chore: auto update rules ({datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')})"
    subprocess.run(["git", "commit", "-m", commit_msg])
    
    # 推送
    # 使用 GITHUB_TOKEN 进行认证
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    push_url = f"https://x-access-token:{token}@github.com/{repo}.git"
    
    try:
        subprocess.run(["git", "push", push_url, "HEAD:main"], check=True)
        print("Pushed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Push failed: {e}")

if __name__ == "__main__":
    process_rules()
    git_commit_push()