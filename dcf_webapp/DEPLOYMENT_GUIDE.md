# Step-by-Step Deployment Guide

This guide will walk you through hosting your DCF Valuation Engine online for **free** using Render.

## Why Render?

- ✅ Completely free tier
- ✅ Easy to use (no complex configuration)
- ✅ Automatic deployments from GitHub
- ✅ HTTPS included
- ✅ Easy to upgrade later when you need more features

## Prerequisites

1. A GitHub account (free) - [Sign up here](https://github.com/signup)
2. A Render account (free) - [Sign up here](https://render.com/signup)
3. Your DCF webapp files (you already have these!)

---

## Part 1: Upload Your Code to GitHub

### Step 1: Create a GitHub Repository

1. Go to [github.com](https://github.com) and log in
2. Click the "+" icon in the top-right corner
3. Select "New repository"
4. Fill in the details:
   - Repository name: `dcf-valuation-engine` (or any name you prefer)
   - Description: "DCF valuation tool for stock analysis"
   - Make it Public (required for free Render hosting)
   - Don't initialize with README (we already have one)
5. Click "Create repository"

### Step 2: Upload Your Files to GitHub

**Option A: Using GitHub's Web Interface (Easiest for Beginners)**

1. On your new repository page, click "uploading an existing file"
2. Drag and drop ALL files from your `dcf_webapp` folder:
   - `app.py`
   - `dcf_code.py`
   - `dcf_loader.py`
   - `requirements.txt`
   - `README.md`
   - `.gitignore`
   - The `templates` folder (with `index.html`)
   - The `static` folder (with `css` and `js` subfolders)
3. Add a commit message: "Initial commit - DCF Valuation Engine"
4. Click "Commit changes"

**Option B: Using Git Command Line (If You're Comfortable with Terminal)**

```bash
# Navigate to your dcf_webapp folder
cd /path/to/dcf_webapp

# Initialize git repository
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit - DCF Valuation Engine"

# Connect to GitHub (replace with your repository URL)
git remote add origin https://github.com/YOUR-USERNAME/dcf-valuation-engine.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Part 2: Deploy to Render

### Step 1: Create a Web Service on Render

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Log in or sign up (you can sign up with your GitHub account)
3. Click the "New +" button
4. Select "Web Service"

### Step 2: Connect Your GitHub Repository

1. Click "Connect account" under GitHub
2. Authorize Render to access your GitHub
3. You should see your `dcf-valuation-engine` repository
4. Click "Connect" next to it

### Step 3: Configure Your Web Service

Fill in the following settings:

- **Name**: `dcf-valuation-engine` (this will be part of your URL)
- **Region**: Choose the one closest to you
- **Branch**: `main`
- **Root Directory**: Leave blank
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

### Step 4: Select Free Plan

- Scroll down to "Instance Type"
- Select **"Free"** (this gives you 512 MB RAM and 0.1 CPU)
- Note: The free tier includes:
  - ✅ Automatic HTTPS
  - ✅ Custom domain support
  - ⚠️ Spins down after 15 minutes of inactivity (wakes up in ~30 seconds)

### Step 5: Add Environment Variables (Optional but Recommended)

If you want to use your own FMP API key:

1. Scroll to "Environment Variables"
2. Click "Add Environment Variable"
3. Key: `FMP_API_KEY`
4. Value: Your API key from Financial Modeling Prep
5. Click "Add"

### Step 6: Deploy!

1. Review all settings
2. Click "Create Web Service"
3. Wait for deployment (usually 2-5 minutes)
4. You'll see logs showing the build process

---

## Part 3: Access Your Live Website

Once deployment is complete:

1. Your app will be live at: `https://dcf-valuation-engine.onrender.com`
   (Replace with your actual service name)
2. Click the URL at the top of your Render dashboard
3. Test it by entering a ticker like "AAPL" and calculating a valuation!

---

## Understanding the Free Tier Limitations

### Cold Starts
- Your app "sleeps" after 15 minutes of inactivity
- First visit after sleep takes ~30 seconds to wake up
- Subsequent visits are instant
- This is perfect for personal projects and learning

### Traffic Limits
- 100 GB bandwidth per month (plenty for most personal use)
- Shared CPU (still fast enough for this application)

### When to Upgrade
Consider upgrading ($7/month) if:
- You want the app to stay "always on" (no cold starts)
- You need custom domains
- You expect high traffic

---

## Troubleshooting

### Deployment Failed?

**Check these common issues:**

1. **Missing requirements.txt**: Make sure it's in the root of your repository
2. **Wrong start command**: Should be `gunicorn app:app`
3. **Python version**: Render uses Python 3.7+ by default (our app is compatible)

### App Loads but Shows Error?

1. Check the Render logs (available in the dashboard)
2. Most common issue: API key problems
   - The hardcoded API key in your code should work
   - But consider adding your own via environment variables

### API Rate Limit Exceeded?

- Free tier of FMP API: 250 requests/day
- Solution: Get your own free API key from [Financial Modeling Prep](https://site.financialmodelingprep.com/developer/docs/)
- Add it as an environment variable in Render

---

## Next Steps - Making Updates

When you want to add features or fix bugs:

### Using GitHub Web Interface:
1. Go to your repository
2. Click on the file you want to edit
3. Click the pencil icon to edit
4. Make changes and commit
5. Render automatically redeploys (takes 2-5 minutes)

### Using Git Command Line:
```bash
# Make your changes to the code
# Then:
git add .
git commit -m "Description of your changes"
git push origin main
```

Render will automatically detect the push and redeploy your app!

---

## Adding Features Later

Your Flask setup makes it easy to expand:

### Add a New Page:
1. Create new HTML template in `templates/`
2. Add route in `app.py`
3. Link from your main page

### Add a Database:
1. Render offers free PostgreSQL databases
2. Connect using SQLAlchemy
3. Store user valuations and preferences

### Add More Models:
1. Create new Python files (e.g., `ddm_code.py`)
2. Add new routes in `app.py`
3. Create new templates

---

## Cost Summary

| Service | Cost | What You Get |
|---------|------|--------------|
| GitHub | FREE | Unlimited public repositories |
| Render (Web Service) | FREE | 512 MB RAM, 0.1 CPU, HTTPS, Custom domains |
| FMP API | FREE | 250 API calls/day |
| **Total** | **$0/month** | Fully functional DCF valuation website |

### Optional Upgrades (When Needed)
- Render Starter: $7/month (always-on, no cold starts)
- FMP API Professional: $14/month (unlimited calls + more data)

---

## Security Best Practices

Before going public, consider:

1. **Move API Key to Environment Variable**
   - Don't hardcode it in `dcf_loader.py`
   - Use `os.environ.get('FMP_API_KEY')`

2. **Add Rate Limiting**
   - Prevents abuse of your free API quota
   - Use Flask-Limiter extension

3. **Add Input Validation**
   - Already partially implemented
   - Consider adding CAPTCHA for public use

---

## Getting Help

- **Render Docs**: [render.com/docs](https://render.com/docs)
- **Flask Docs**: [flask.palletsprojects.com](https://flask.palletsprojects.com/)
- **FMP API Docs**: [site.financialmodelingprep.com/developer/docs](https://site.financialmodelingprep.com/developer/docs/)

---

## Congratulations!

You now have a live, professional DCF valuation website that you can:
- Share with friends and on your resume
- Use for your own stock analysis
- Expand with new features over time
- Upgrade when you need more capacity

**Your website is now accessible to anyone in the world!** 🎉
