import requests
import re
import os
import datetime

# 配置源地址
URLS = {
    "dns": "https://filters.adtidy.org/android/filters/15_optimized.txt",
    "base": "https://filters.adtidy.org/android/filters/2_optimized.txt",
    "chinese": "https://filters.adtidy.org/android/filters/224_optimized.txt",
    "tracking": "https://filters.adtidy.org/android/filters/3_optimized.txt",
    "privacy": "https://filters.adtidy.org/android/filters/118_optimized.txt",
    "social": "https://filters.adtidy.org/android/filters/4_optimized.txt",
    "annoys": "https://filters.adtidy.org/android/filters/14_optimized.txt"
}

# 输出文件配置
FILES_CONFIG = {
    "adgdns.txt": {
        "title": "AdGuard Domain",
        "description": "Merge AdGuard DNS & Chinese Filter"
    },
    "adgads.txt": {
        "title": "AdGuard Advert",
        "description": "Merge AdGuard Base & Chinese Filter"
    },
    "adgany.txt": {
        "title": "AdGuard Annoys",
        "description": "Merge AdGuard Annoys & Social Filter"
    },
    "adgprv.txt": {
        "title": "AdGuard Privacy",
        "description": "Merge AdGuard Tracking & EasyPrivacy"
    }
}

# 正则匹配规则
# 域名级规则特征：以 || 开头，中间没有 /，以 ^ 结尾 (可能带有 $ 选项)
REGEX_DOMAIN = re.compile(r'^\|\|[^/$]+\^(\$.*)?$')

def fetch_content(url):
    """获取远程文件内容"""
    print(f"Fetching: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text.splitlines()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def parse_rules(lines):
    """解析规则，分为域名级和路径级"""
    domains = set()
    paths = set()
    
    for line in lines:
        line = line.strip()
        # 跳过空行和注释
        if not line or line.startswith('!') or line.startswith('#'):
            continue
        # 跳过非网络规则 (如 cosmetic filters ##, #@# 等)
        if not line.startswith('||'):
            paths.add(line)
            continue
            
        # 判断是域名级还是路径级
        if REGEX_DOMAIN.match(line):
            domains.add(line)
        else:
            paths.add(line)
            
    return domains, paths

def write_file(filename, rules, config):
    """写入文件，带自定义头部信息"""
    sorted_rules = sorted(list(rules))
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    with open(filename, "w", encoding="utf-8") as f:
        # 基础信息
        f.write(f"! Title: {config['title']}\n")
        f.write(f"! Description: {config['description']}\n")
        f.write(f"! Total Rules: {len(sorted_rules)}\n")
        f.write(f"! Updated: {timestamp}\n")
        f.write(f"! Expires: 5 days\n")
        f.write("!\n")
        
        # 规则内容
        for rule in sorted_rules:
            f.write(f"{rule}\n")
            
    print(f"Generated {filename} with {len(sorted_rules)} rules.")

def main():
    # 1. 拉取数据
    dns_lines = fetch_content(URLS["dns"])
    base_lines = fetch_content(URLS["base"])
    chinese_lines = fetch_content(URLS["chinese"])
    tracking_lines = fetch_content(URLS["tracking"])
    privacy_lines = fetch_content(URLS["privacy"])
    social_lines = fetch_content(URLS["social"])
    annoys_lines = fetch_content(URLS["annoys"])
    
    # 2. 解析分类
    cn_domains, cn_paths = parse_rules(chinese_lines)
    dns_domains = parse_rules(dns_lines) 
    base_paths = parse_rules(base_lines)
    trk_paths = parse_rules(tracking_lines)
    prv_paths = parse_rules(privacy_lines)
    soc_paths = parse_rules(social_lines)
    ano_paths = parse_rules(annoys_lines)
    
    # 3. 合并逻辑
    final_dns = dns_domains.union(cn_domains)
    
    final_ads = base_paths.union(cn_paths)
    
    final_any = ano_paths.union(soc_paths)
    
    final_prv = trk_paths.union(prv_paths)
        
    # 4. 生成文件 (使用不同的配置)
    write_file("adgdns.txt", final_dns, FILES_CONFIG["adgdns.txt"])
    write_file("adgads.txt", final_ads, FILES_CONFIG["adgads.txt"])
    write_file("adgany.txt", final_any, FILES_CONFIG["adgany.txt"])
    write_file("adgprv.txt", final_ads, FILES_CONFIG["adgprv.txt"])
    
    print("\n✓ All rules updated successfully!")

if __name__ == "__main__":
    main()