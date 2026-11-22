# Grimentz snow dashboard

- `site/index.html`  the dashboard (reads `data.json` next to it)
- `site/data.json`   sample data; replaced by fresh meteoblue data on every deploy
- `fetch_meteoblue.py`  calls the meteoblue API (key from the METEOBLUE_API_KEY secret)
- `.github/workflows/update.yml`  fetches data 3x a day and publishes to GitHub Pages

Setup: create a public GitHub repo with these files, add the secret METEOBLUE_API_KEY
(Settings > Secrets and variables > Actions), set Pages source to "GitHub Actions"
(Settings > Pages), then run the workflow once from the Actions tab.
Local preview: cd site && python3 -m http.server 8000
