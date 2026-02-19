cat > README.md <<'MD'
# 🔎 Intercom Explorer

A simple **scan-style** web explorer for the **Trac-Systems/awesome-intercom** ecosystem — built to browse forks, filter projects, and inspect repo stats in a clean UI.

> Inspired by Etherscan/BaseScan layout, but kept lightweight and easy to run on **Termux**.

---

## ✨ Features

- Explorer-style UI (navbar + search like a scan)
- Search by repo name / description
- Filter: **Intercom** / **IntercomSwap**
- Sort: Stars / Updated / Repo name
- Pagination (mobile friendly)
- Optional GitHub API enrichment (stars, forks, updated_at)

---

## ⚙️ Installation (Termux)

```bash
pkg update -y && pkg upgrade -y
pkg install -y git python
pip install -U pip
pip install flask requests
git clone https://github.com/novareski485/Intercom-explorer.git
cd Intercom-explorer
python app.py

📦 Data Source
Trac-Systems/awesome-intercom (README curated list)
🛣️ Roadmap
[ ] Repo detail page (like “address page” on scan sites)
[ ] Export results to JSON/CSV
[ ] Deploy guide (Render/Vercel/Railway)

🛣️ Roadmap
[ ] Repo detail page (like “address page” on scan sites)
[ ] Export results to JSON/CSV
[ ] Deploy guide (Render/Vercel/Railway)

📄 License
MIT MD
---

### 3) Commit + push
```bash
git add README.md
git commit -m "Replace README with Intercom Explorer scan-style description"
git push origin main
