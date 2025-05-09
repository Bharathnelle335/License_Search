import requests
import pandas as pd

def try_maven_license(component, version):
    from bs4 import BeautifulSoup
    try:
        if ':' not in component:
            return 'invalid', 'unknown', 'missing_groupId'
        group_id, artifact_id = component.split(':')
        group_path = group_id.replace('.', '/')
        url = f"https://repo1.maven.org/maven2/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'xml')
            license_block = soup.find('license')
            if license_block:
                name_tag = license_block.find('name')
                license_name = name_tag.text.strip() if name_tag else 'found'
                return license_name, url, 'maven_fallback'
            licenses_block = soup.find('licenses')
            if licenses_block:
                name_tag = licenses_block.find('name')
                license_name = name_tag.text.strip() if name_tag else 'found'
                return license_name, url, 'maven_fallback'
        return 'unknown', url, 'not_found'
    except Exception as e:
        return 'unknown', 'unknown', f'maven_failed: {e}'
def detect_licenses(input_xlsx, output_xlsx, progress):
    df = pd.read_excel(input_xlsx)
    results = []
    progress['total'] = len(df)
    progress['current'] = 0
    for _, row in df.iterrows():
        component = str(row.get('component_name', '')).strip()
        version = str(row.get('version', '')).strip()
        license_name, license_url, method = try_maven_license(component, version)
        results.append({
            'component_name': component,
            'version': version,
            'final_license': license_name,
            'final_license_url': license_url,
            'detection_method': method
        })
        progress['current'] += 1
    df_all = pd.DataFrame(results)
    df_success = df_all[df_all['final_license'] != 'unknown']
    df_failed = df_all[df_all['final_license'] == 'unknown']
    with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
        df_all.to_excel(writer, index=False, sheet_name='All')
        df_success.to_excel(writer, index=False, sheet_name='Success')
        df_failed.to_excel(writer, index=False, sheet_name='Failed')