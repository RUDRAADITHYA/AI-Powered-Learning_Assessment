# Render Deployment Guide

This guide walks you through deploying the Adaptive Diagnostic Engine to Render in 5 minutes.

## Prerequisites

- ✅ GitHub account (free at [github.com](https://github.com))
- ✅ Render account (free at [render.com](https://render.com))
- ✅ MongoDB Atlas account (free at [mongodb.com/cloud](https://mongodb.com/cloud))
- ✅ Groq API key (free at [console.groq.com/keys](https://console.groq.com/keys))

---

## Step 1: Push Code to GitHub

1. Create a new GitHub repository at https://github.com/new
   - Name: `adaptie-diagnostist`
   - Don't initialize with README

2. Run these commands:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/adaptie-diagnostist.git
   git branch -M main
   git push -u origin main
   ```

**Expected output:** ✅ Repository pushed successfully

---

## Step 2: Get Your MongoDB URI

1. Go to https://cloud.mongodb.com and log in
2. Click **Database** → Select your cluster
3. Click **"Connect"** → **"Drivers"**
4. Select **"Python"** → **"3.12 or later"**
5. Copy the connection string that looks like:
   ```
   mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

**Save this for Step 4.**

---

## Step 3: Get Your Groq API Key

1. Go to https://console.groq.com/keys
2. Generate a new API key (if you don't have one)
3. Copy the key (looks like: `gsk_xxxxxxxxxxxxx`)

**Save this for Step 4.**

---

## Step 4: Deploy on Render

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Click **"Connect a repository"**
4. Find and select `adaptie-diagnostist`
5. Fill in the form:
   - **Name**: `adaptie-diagnostist` (this becomes your domain: `adaptie-diagnostist-xxxx.onrender.com`)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (or Paid for always-on)

6. Click **"Create Web Service"** (don't worry if it fails, we need to add env vars first)

7. Once created, go to **Settings** → **Environment Variables**
   - Click **"Add Environment Variable"** and add these four:

   | Key | Value |
   |-----|-------|
   | `MONGODB_URI` | (paste your MongoDB URI from Step 2) |
   | `GROQ_API_KEY` | (paste your API key from Step 3) |
   | `DATABASE_NAME` | `adaptive_diagnostic` |
   | `APP_NAME` | `Adaptive-Diagnostist` |

8. Click **"Save Changes"** and Render will automatically redeploy

---

## Step 5: Verify Deployment

Once the deploy completes (watch the log), your app is live at:

```
https://adaptie-diagnostist-xxxx.onrender.com
```

**Test it:**
1. Open the link in your browser
2. Click **"Register"** and create a test account
3. Select **"Algebra"** difficulty **"Medium"**, and **10 Questions**
4. Click **"Start Test"** ✅

---

## Troubleshooting

### Build Failed: "ModuleNotFoundError"
**Solution:** The `requirements.txt` already has all dependencies. If still failing, check Render's build logs.

### MongoDB Connection Error
**Solution:** 
1. Verify your `MONGODB_URI` in Render Settings
2. Go to MongoDB Atlas → Security → Network Access
3. Add IP address `0.0.0.0/0` to allow all Render IPs

### Groq API Error
**Solution:** Verify `GROQ_API_KEY` is correct (no extra spaces or quotes)

### App Shows "Service Unavailable"
**Solution:** 
1. Check the Render logs (at the bottom of the deploy details)
2. Wait 2-3 minutes for the service to fully boot on a free plan

---

## Next Steps

- **Enable Auto-Deploy:** In Render Settings, enable "Auto-Deploy from Git" so updates automatically deploy when you push to GitHub
- **Monitor Performance:** Check Render's metrics dashboard for uptime and response times
- **Custom Domain:** Add your own domain via Render's custom domain settings

---

## Support

If issues persist:
1. Check [Render Docs](https://render.com/docs)
2. Check [MongoDB Atlas Docs](https://docs.mongodb.com/drivers/motor/)
3. Check [FastAPI Docs](https://fastapi.tiangolo.com/)
