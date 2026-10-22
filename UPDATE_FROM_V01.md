# Updating your existing ~/Desktop/barberos-mvp project

1. **Stop both local servers** with Ctrl+C. If you have uncommitted work, commit or back it up first.
2. Download/extract the `BarberOS-Aaron-MVP.zip` file next to your existing `barberos-mvp` folder (for example into `~/Downloads/BarberOS-Aaron-MVP`).
3. Open a terminal and merge the source code, **without replacing your `.git` history, `.env` or local DB**:

   ```bash
   cd ~/Desktop/barberos-mvp
   rsync -av \
     --exclude '.git/' \
     --exclude '.venv/' \
     --exclude 'node_modules/' \
     --exclude '*.db' \
     --exclude '.env' \
     ~/Downloads/BarberOS-Aaron-MVP/ ./
   ```

   **Note:** If the extracted folder is called `BarberOS-Aaron-MVP` in another location, replace the example source path. `rsync` is additive and does not delete unmentioned files.
4. If your existing `frontend/.env` contains `VITE_SHOP_SLUG=northside`, change it to `VITE_SHOP_SLUG=aaron-binions` (or remove that setting). Verify `backend/app/seed.py`, `frontend/src/pages/Storefront.jsx`, and `frontend/public/media/aaron-portrait.webp` exist.
5. Run backend:

   ```bash
   cd ~/Desktop/barberos-mvp/backend
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   python -m uvicorn app.main:app --reload
   ```

6. In another terminal, run frontend:

   ```bash
   cd ~/Desktop/barberos-mvp/frontend
   npm install
   npm run dev
   ```

7. Open http://localhost:5173. Use the **local pilot** bar to view both the site and dashboard. Your existing SQLite database stays intact and a separate Aaron shop is created on the first backend start.
8. Test a haircut booking and then see it in the admin dashboard. Change a demo hour and confirm the time slots update.
9. When satisfied, from the repo root:

   ```bash
   git status
   git add .
   git commit -m "feat: Aaron Binions private studio pilot"
   git remote -v
   git push -u origin main
   ```

   If you have not connected Git yet, add your repo first:

   ```bash
   git init
   git branch -M main
   git remote add origin https://github.com/Ruairi922/BarberOS.git
   ```

**Before pushing to a public repo:** the site package includes cropped images and review screenshots taken from Aaron's social account. Check that he agrees to storing/publishing these assets, and remove anything he doesn't want published. Never commit `.env`, `.venv`, database files or customer details.
