# 📚 License Search Webapps (Ubuntu | NPM | Maven | PyPI)

This repository provides license detection tools for multiple ecosystems using Python + Web UI. It supports **Ubuntu**, **NPM**, **Maven**, and **PyPI** components. Each subfolder contains a fully working webapp that:

- Accepts an Excel file with component names + versions.
- Detects licenses via APIs, metadata files, or fallbacks.
- Exports an Excel report with structured results.
- Has a clean, centered UI with upload, progress, and download options.

---

## 📁 Folder Structure

| Folder Name                       | Ecosystem | Detects From                                    | UI Title             |
|----------------------------------|-----------|-------------------------------------------------|----------------------|
| `ubuntu_license_webapp_cleaned_final` | Ubuntu    | Ubuntu changelogs, Debian metadata               | Ubuntu License Tool  |
| `npm_license_webapp_only_fixed_ui`   | NPM       | NPM Registry, GitHub fallback                    | NPM License Tool     |
| `maven_license_webapp_final_v2`      | Maven     | Maven Central (pom.xml parsing)                 | Maven License Tool   |
| `pypi_license_webapp_final_ready`    | PyPI      | PyPI API, project homepage fallback             | PyPI License Tool    |

---

## 📦 Requirements

Each folder includes a `requirements.txt`. General dependencies across all:

```txt
Flask
openpyxl
pandas
requests
beautifulsoup4
lxml
```

To install:

```bash
pip install -r requirements.txt
```

Make sure `lxml` is installed to parse XML in Maven and PyPI tools:
```bash
pip install lxml
```

---

## 🚀 How to Run Any Tool

```bash
cd <target_folder>
pip install -r requirements.txt
python app.py
```

Then open your browser at:  
[http://localhost:5000](http://localhost:5000)

---

## 📥 Input Excel Format

All tools expect an Excel file with the following structure:

| component_name                     | version        |
|-----------------------------------|----------------|
| org.springframework:spring-core   | 5.3.27.RELEASE |
| com.google.guava:guava            | 32.1.2-jre     |

> For Maven, format must be `group:artifact`.

---

## 📤 Output Excel Structure

Each tool generates an Excel file with 3 sheets:

### Sheet: `All`

| Column               | Description                                              |
|----------------------|----------------------------------------------------------|
| component_name       | Name of the package                                      |
| version              | Version from input                                       |
| final_license        | Detected license name (e.g., MIT, GPL-2.0)               |
| final_license_url    | URL pointing to license page or metadata file            |
| detection_method     | Which method detected it (`api`, `fallback`, etc.)       |
| version_check        | Whether version matches found metadata                   |
| error_reason         | If failed, this shows the reason (404, parse issue, etc.)|

### Sheet: `Success`
Only components with valid licenses.

### Sheet: `Failed`
Only components where license could not be detected.

---

## 💡 Future Improvements

- Add SPDX normalization.
- Add vulnerability scanning hooks.
- Export SPDX/JSON in addition to Excel.

---

## 🙋‍♂️ Maintained By

**Bharath N.**  
🔗 GitHub: [Bharathnelle335](https://github.com/Bharathnelle335)
