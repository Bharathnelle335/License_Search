import requests
import pandas as pd
import os
import re

def extract_license_from_text(text):
    for line in text.splitlines():
        if 'License:' in line:
            return line.split('License:')[1].strip(), 'license_phrase'
        match = re.search(r'SPDX-License-Identifier:\s*([A-Za-z\-\.0-9+]+)', line)
        if match:
            return match.group(1), 'spdx_identifier'
    return 'unknown', 'fallback_failed'

def try_npmjs_license(package, version):
    try:
        url = f"https://registry.npmjs.org/{package}/{version}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            license = data.get("license", "")
            if isinstance(license, dict):
                license = license.get("type", "")
            license_url = f"https://www.npmjs.com/package/{package}/v/{version}"
            return license or "unknown", license_url, "npm_fallback"
    except:
        pass
    return "unknown", "unknown", "npm_failed"

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
            if href and "npmjs.com/package" in href:
                links.append(href)
            if len(links) >= max_results:
                break
        return links
    except:
        return []

def detect_licenses(input_xlsx, output_xlsx, progress):
    df = pd.read_excel(input_xlsx)
    results = []
    progress['total'] = len(df)
    progress['current'] = 0

    for _, row in df.iterrows():
        name = str(row.get('component_name', '')).strip()
        version = str(row.get('version', '')).strip()

        license_name, license_url, method = try_npmjs_license(name, version)
        error_reason = ''

        if license_name == 'unknown':
            query = f"{name} {version} license site:npmjs.com"
            search_links = duckduckgo_search(query)
            for link in search_links:
                try:
                    res = requests.get(link, timeout=10)
                    if res.status_code == 200:
                        license_name, method = extract_license_from_text(res.text)
                        if license_name != 'unknown':
                            license_url = link
                            error_reason = 'fetched via duckduckgo'
                            break
                except:
                    continue
            if license_name == 'unknown':
                error_reason = 'license not found'

        results.append({
            'component_name': name,
            'version': version,
            'final_license': license_name,
            'final_license_url': license_url,
            'detection_method': method,
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