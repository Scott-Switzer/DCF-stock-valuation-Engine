# Secure Deployment Guide - API Key Protected

## ⚠️ SECURITY FIRST

Your API key should **NEVER** be in your code or on GitHub. Here's how to do it right.

---

## Part 1: Get a New API Key

Since your previous key may have been exposed:

1. Go to [Financial Modeling Prep](https://site.financialmodelingprep.com/developer/docs/)
2. Log in to your account
3. Go to your Dashboard → API Keys
4. **Delete your old key** or generate a new one
5. Copy the new API key (you'll need it soon)

---

## Part 2: Set Up Locally (For Testing)

### Option A: Using Environment Variables (Mac/Linux)

1. Open Terminal
2. Navigate to your project folder:
   ```bash
   cd path/to/dcf_webapp
   ```

3. Create a `.env` file:
   ```bash
   echo "FMP_API_KEY=your_actual_api_key_here" > .env
   ```
   ⚠️ Replace `your_actual_api_key_here` with your real key!

4. Install python-dotenv:
   ```bash
   pip install python-dotenv
   ```

5. Test locally:
   ```bash
   export FMP_API_KEY=your_actual_api_key_here
   python app.py
   ```

### Option B: Set Environment Variable (Windows)

1. Open Command Prompt
2. Navigate to your project:
   ```cmd
   cd path\to\dcf_webapp
   ```

3. Set the environment variable:
   ```cmd
   set FMP_API_KEY=your_actual_api_key_here
   python app.py
   ```

---

## Part 3: Upload to GitHub (Safely)

### Step 1: Initialize Git Repository

```bash
cd dcf_webapp
git init
git add .
git commit -m "Initial commit - DCF Valuation Engine"
```

**IMPORTANT**: The `.gitignore` file ensures `.env` is never uploaded!

### Step 2: Create GitHub Repository

1. Go to [github.com](https://github.com) and create a new repository
2. Name it `dcf-valuation-engine`
3. Make it **Public** (required for free Render hosting)
4. **DO NOT** add README, .gitignore, or license (we already have them)

### Step 3: Push to GitHub

```bash
git remote add origin https://github.com/YOUR-USERNAME/dcf-valuation-engine.git
git branch -M main
git push -u origin main
```

### Step 4: Verify Security

1. Go to your GitHub repository
2. Browse the files
3. **Confirm** there is NO API key in `dcf_loader.py` or `app.py`
4. **Confirm** `.env` file is NOT visible (it should be ignored)

---

## Part 4: Deploy to Render (With Secret API Key)

### Step 1: Create Web Service

1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository

### Step 2: Configure Service

Fill in:
- **Name**: `dcf-valuation-engine`
- **Environment**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Plan**: Free

### Step 3: Add Environment Variable (CRITICAL!)

This is where you securely add your API key:

1. Scroll to "Environment Variables" section
2. Click "Add Environment Variable"
3. Enter:
   - **Key**: `FMP_API_KEY`
   - **Value**: `[Paste your actual API key here]`
4. Click "Add"

**This keeps your key secret!** It's stored securely on Render's servers and never visible in your code.

### Step 4: Deploy

Click "Create Web Service" and wait for deployment.

---

## Part 5: Testing Your Secure Setup

1. Once deployed, visit your Render URL
2. Try calculating a DCF for "AAPL"
3. If it works, your API key is properly configured! ✅

---

## How This Security Works

```
❌ BAD (Old Way):
   Code → Contains API Key → Uploaded to GitHub → Key is PUBLIC!

✅ GOOD (New Way):
   Code → Uses Environment Variable → Uploaded to GitHub → No secrets!
   Render → Environment Variable Set → Key is PRIVATE!
```

---

## Common Questions

### Q: What if someone sees my code on GitHub?
**A:** They'll see the code uses an environment variable, but they won't see your actual key. They'd need to add their own key to run it.

### Q: Can I still test locally?
**A:** Yes! Set the environment variable on your computer before running the app.

### Q: What if I accidentally committed my API key?
**A:** 
1. Delete the repository immediately
2. Regenerate your API key
3. Start fresh with this secure setup

### Q: Do I need to pay for environment variables on Render?
**A:** No! Environment variables are free on all Render plans.

---

## Local Development Quick Commands

### Mac/Linux:
```bash
export FMP_API_KEY=your_key_here
python app.py
```

### Windows:
```cmd
set FMP_API_KEY=your_key_here
python app.py
```

### Using .env file (Recommended):
1. Create `.env` file with: `FMP_API_KEY=your_key_here`
2. Install: `pip install python-dotenv`
3. Add to `app.py` at the top:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```
4. Run: `python app.py`

---

## Checklist Before Pushing to GitHub

- [ ] Removed all hardcoded API keys from code
- [ ] Created `.gitignore` file (included in your download)
- [ ] Verified `.env` is in `.gitignore`
- [ ] API key only exists in environment variables
- [ ] Tested locally with environment variable
- [ ] Ready to push!

---

## 🎉 You're Now Secure!

Your API key is protected, and you can safely share your code on GitHub without exposing sensitive credentials.

**Remember**: Environment variables are the industry-standard way to handle secrets in web applications.
