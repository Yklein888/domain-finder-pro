# Vercel Frontend Deployment

## שלב 1: Connect to GitHub
1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Select "Import Git Repository"
4. Choose: `Yklein888/domain-finder-pro`

## שלב 2: Configure
- **Root Directory**: `frontend`
- **Framework**: None (Static HTML)
- **Build Command**: (leave empty)
- **Output Directory**: (leave empty)

## שלב 3: Environment Variables
```
REACT_APP_API_URL=https://domain-finder-pro-xxxxx.run.app
```
(Replace with your Cloud Run URL)

## שלב 4: Deploy
Click "Deploy" - Vercel will build and deploy automatically

## תוצאה
- **URL**: `https://domain-finder-pro.vercel.app` (or custom domain)
- Auto-deploys on every git push
- Global CDN for fast loading

---

## עדכון API URL בדashboard

1. Open dashboard: `https://domain-finder-pro.vercel.app`
2. Go to Settings tab
3. Enter Backend URL: `https://domain-finder-pro-xxxxx.run.app`
4. Click Save

זה הכל! 🎉
