import requests
import pandas as pd

def detect_licenses(input_xlsx, output_xlsx, progress):
    df = pd.read_excel(input_xlsx)
    results = []
    progress['total'] = len(df)
    progress['current'] = 0

    for _, row in df.iterrows():
        component = str(row.get('component_name', '')).strip()
        version = str(row.get('version', '')).strip()
        license_name, license_url, method = 'unknown', 'unknown', 'not_found'
        try:
            url = f"https://pypi.org/pypi/{component}/{version}/json"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                license_name = data['info'].get('license', 'unknown').strip()
                license_url = f"https://pypi.org/project/{component}/{version}/"
                method = 'pypi_api'
        except Exception as e:
            method = f"pypi_failed: {str(e)}"

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