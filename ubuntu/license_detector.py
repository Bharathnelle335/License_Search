import requests
import pandas as pd
import os
import gzip
import re

PACKAGE_MAP_URL = "https://archive.ubuntu.com/ubuntu/dists/focal/main/binary-amd64/Packages.gz"
PACKAGE_MAP_LOCAL = "packages_focal.gz"
binary_to_source_map = {}

def download_and_parse_package_map():
    global binary_to_source_map
    if not os.path.exists(PACKAGE_MAP_LOCAL):
        res = requests.get(PACKAGE_MAP_URL, timeout=20)
        with open(PACKAGE_MAP_LOCAL, 'wb') as f:
            f.write(res.content)
    with gzip.open(PACKAGE_MAP_LOCAL, 'rt', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    current_pkg = None
    for line in lines:
        if line.startswith("Package:"):
            current_pkg = line.split(":", 1)[1].strip()
        elif line.startswith("Source:") and current_pkg:
            src = line.split(":", 1)[1].strip()
            binary_to_source_map[current_pkg] = src
            current_pkg = None
        elif line.strip() == "" and current_pkg:
            binary_to_source_map[current_pkg] = current_pkg
            current_pkg = None

def get_source_name(binary_name):
    if not binary_to_source_map:
        download_and_parse_package_map()
    return binary_to_source_map.get(binary_name, binary_name)

def sanitize_version(version):
    return version.split(':')[-1] if ':' in version else version

def extract_license_from_text(text):
    for line in text.splitlines():
        if 'License:' in line:
            return line.split('License:')[1].strip(), 'ubuntu_changelog'
        match = re.search(r'SPDX-License-Identifier:\s*([A-Za-z\-\.0-9+]+)', line)
        if match:
            return match.group(1), 'spdx_identifier'
        if any(keyword in line.lower() for keyword in ['license', 'licensed under']):
            match_generic = re.search(r'under the (.*?) license', line, re.IGNORECASE)
            if match_generic:
                return match_generic.group(1), 'license_phrase'
    return 'unknown', 'fallback_failed'

def safe_request(url, max_retries=3):
    headers = { 'User-Agent': 'Mozilla/5.0' }
    last_error = ""
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Trying URL (attempt {attempt}): {url}")
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                print(f"✅ Success: {url}")
                return res
            else:
                last_error = f"HTTP {res.status_code} at {url}"
                print(f"❌ Failed: {last_error}")
        except Exception as e:
            last_error = f"Exception: {str(e)} at {url}"
            print(f"❌ Error: {last_error}")
    return last_error

def duckduckgo_search(query, max_results=5):
    from bs4 import BeautifulSoup
    headers = { "User-Agent": "Mozilla/5.0" }
    url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return []
        soup = BeautifulSoup(res.text, "html.parser")
        links = []
        for a in soup.select("a.result__a"):
            href = a.get("href")
            if href and any(x in href for x in ["ubuntu.com", "debian.org", "changelogs"]):
                links.append(href)
            if len(links) >= max_results:
                break
        return links
    except:
        return []

def get_source_and_version_from_packages(binary_name):
    path = "packages_focal.gz"
    if not os.path.exists(path):
        print("⏳ Downloading packages_focal.gz...")
        url = "https://archive.ubuntu.com/ubuntu/dists/focal/main/binary-amd64/Packages.gz"
        res = requests.get(url, timeout=30)
        with open(path, 'wb') as f:
            f.write(res.content)
    with gzip.open(path, 'rt', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    current_pkg = None
    source = ""
    src_ver = ""
    for line in lines:
        if line.startswith("Package:"):
            current_pkg = line.split(":", 1)[1].strip()
        elif line.startswith("Source:") and current_pkg == binary_name:
            parts = line.split(":", 1)[1].strip().split()
            source = parts[0]
            if len(parts) > 1:
                src_ver = parts[1].strip("()")
        elif line.startswith("Version:") and current_pkg == binary_name and not src_ver:
            src_ver = line.split(":", 1)[1].strip()
        elif line.strip() == "" and current_pkg == binary_name:
            return source or binary_name, src_ver
    return binary_name, ""

def build_url_patterns(source, version):
    v = version.split(':')[-1] if ':' in version else version
    first = source[0]
    prefix = source[:4] if source.startswith('lib') else first
    lib_dir = f"lib{source[3]}" if source.startswith("lib") and len(source) > 3 else first
    variants = list(set([
        source,
        source.replace('-', '_'),
        source.replace('_', '-'),
        source.rstrip('0123456789'),
        re.sub(r'-dev$', '', source),
    ]))
    urls = []
    for name in variants:
        for folder in [first, lib_dir, prefix]:
            urls.append(f"https://changelogs.ubuntu.com/changelogs/pool/main/{folder}/{name}/{name}_{v}/copyright")
            urls.append(f"https://changelogs.ubuntu.com/changelogs/pool/main/{folder}/{name}/copyright")
        urls.append(f"https://metadata.ftp-master.debian.org/changelogs/main/{first}/{name}/{name}_{v}/copyright")
        urls.append(f"https://metadata.ftp-master.debian.org/changelogs/main/{first}/{name}/{name}_{v}_copyright")
        urls.append(f"https://metadata.ftp-master.debian.org/changelogs/main/{first}/{name}/copyright")
    return list(dict.fromkeys(urls))[:20]

def get_debian_source_info(pkg_name):
    try:
        url = f"https://packages.debian.org/source/sid/{pkg_name}"
        res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200:
            match = re.search(r"Source Package:.*?<a.*?>(.*?)</a>.*?\((.*?)\)", res.text, re.DOTALL)
            if match:
                return match.group(1).strip(), match.group(2).strip()
        url = f"https://packages.debian.org/sid/{pkg_name}"
        res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        match = re.search(r"Source Package:.*?<a.*?>(.*?)</a>.*?\((.*?)\)", res.text, re.DOTALL)
        if match:
            return match.group(1).strip(), match.group(2).strip()
    except:
        pass
    return pkg_name, ""

def get_debian_source_version(source):
    try:
        url = f"https://sources.debian.org/api/src/{source}/"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if 'versions' in data and len(data['versions']) > 0:
                return data['versions'][0]['version']
    except:
        pass
    return ""

def try_debian_sources(binary_name):
    source, version = get_debian_source_info(binary_name)
    debian_ver = get_debian_source_version(source)
    base_urls = [
        f"https://sources.debian.org/src/{source}/{debian_ver}/debian/copyright",
        f"https://sources.debian.org/src/{source}/{version}/debian/copyright",
        f"https://metadata.ftp-master.debian.org/changelogs/main/{source[0]}/{source}/{source}_{version}_copyright"
    ]
    for url in base_urls:
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if res.status_code == 200 and 'License' in res.text:
                for line in res.text.splitlines():
                    if 'License:' in line:
                        return line.split("License:")[1].strip(), url, 'debian_fallback'
                return 'found in debian', url, 'debian_fallback'
        except:
            continue
    return 'unknown', 'unknown', 'debian_failed'

def detect_licenses(input_xlsx, output_xlsx, progress):
    df = pd.read_excel(input_xlsx)
    results = []
    progress['total'] = len(df)
    progress['current'] = 0
    for _, row in df.iterrows():
        binary_name = str(row.get('component_name', '')).strip()
        version = str(row.get('version', '')).strip()
        source_name, source_version = get_source_and_version_from_packages(binary_name)
        license_name, license_url, method, error_reason = 'unknown', 'unknown', 'failed', 'no valid pattern matched'

        for url in build_url_patterns(source_name, source_version):
            res = safe_request(url)
            if isinstance(res, str):
                error_reason = res
                continue
            if res:
                text = res.text
                license_name, method = extract_license_from_text(text)
                if license_name != 'unknown':
                    license_url = url
                    error_reason = ''
                    break
                else:
                    error_reason = 'valid URL, no license pattern'
            else:
                error_reason = 'URL not reachable'

        if license_name == 'unknown':
            license_name, license_url, method = try_debian_sources(binary_name)
            if license_name != 'unknown':
                error_reason = 'matched via debian fallback'

        results.append({
            'component_name': binary_name,
            'version': version,
            'final_license': license_name,
            'final_license_url': license_url,
            'detection_method': method,
            'version_check': 'yes' if sanitize_version(version) in license_url else 'no',
            'source_name_used': source_name,
            'error_reason': error_reason
        })
        progress['current'] += 1

    df_all = pd.DataFrame(results)
    df_success = df_all[df_all['final_license'] != 'unknown']
    df_failed = df_all[df_all['final_license'] == 'unknown']

    with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
        df_all.to_excel(writer, index=False, sheet_name='All')
        df_success.to_excel(writer, index=False, sheet_name='Success')
        df_failed.to_excel(writer, index=False, sheet_name='Failed')