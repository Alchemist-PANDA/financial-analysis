# 🚀 100% Free Deployment Guide: Financial Agent Terminal

This guide explains how to host your AI Agent Terminal for **$0.00/month** using the "Zero Cost Stack": **Neon** (Database), **Render** (Backend), and **Vercel** (Frontend).

---

## 🏗️ The Zero Cost Stack
| Component | Provider | Why? |
| :--- | :--- | :--- |
| **Database** | [Neon.tech](https://neon.tech) | Free Serverless Postgres with persistence. |
| **Backend** | [Render.com](https://render.com) | Free Docker hosting for FastAPI. |
| **Frontend** | [Vercel.com](https://vercel.com) | Best-in-class free hosting for Next.js. |

---

## 1. 🐘 Setup Database (Neon)
1. Go to [Neon.tech](https://neon.tech) and create a free account.
2. Create a new project called `financial-agent`.
3. In the **Dashboard**, copy your **Connection String**.
   - Select **Pooled connection** (looks like `postgres://user:pass@ep-pool...`).
4. Save this as `DATABASE_URL`.

---

## 2. 🐍 Setup Backend (Render)
1. Push your code to a **GitHub repository**.
2. Go to [Render.com](https://render.com) and sign in.
3. Click **New +** > **Web Service**.
4. Connect your GitHub repo.
5. Configure the service:
   - **Name**: `financial-agent-backend`
   - **Environment**: `Docker`
   - **Dockerfile Path**: `Dockerfile.backend`
   - **Plan**: `Free`
6. Click **Advanced** and add **Environment Variables**:
   - `DATABASE_URL`: (The string from Neon)
   - `GROQ_API_KEY`: (Your key)
   - `GOOGLE_API_KEY`: (Your key)
   - `TAVILY_API_KEY`: (Your key)
   - `API_SECRET_KEY`: (A random password for your API)
7. Click **Create Web Service**. 
   - *Note: It will take a few minutes to build. Once live, you will get a URL like `https://xxx.onrender.com`.*

---

## ⚛️ 3. Setup Frontend (Vercel)
1. Go to [Vercel.com](https://vercel.com) and sign in.
2. Click **Add New** > **Project**.
3. Import your GitHub repo.
4. Configure the project:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: `frontend-next`
5. Add **Environment Variables**:
   - `NEXT_PUBLIC_API_URL`: (Your Render URL, e.g., `https://xxx.onrender.com`)
   - `API_SECRET_KEY`: (The SAME password you set for the backend)
6. Click **Deploy**.

---

## ⚠️ Important Limitations of Free Tiers

> [!IMPORTANT]
> **Render Sleep Mode**: Render's free tier spins down after 15 minutes of inactivity. When you first visit your dashboard after some time, it may take 30-60 seconds for the backend to "wake up". This is normal for free hosting.

> [!TIP]
> **Database Persistence**: Because we use **Neon**, your analysis history and watchlist will be saved forever, even when the Render backend restarts.

---

## 🔒 Security Checklist
1. Never commit your `.env` file to GitHub.
2. Ensure `API_SECRET_KEY` is long and unique.
3. If using in production, restrict CORS in `app/api.py` to only allow your Vercel domain.

---

## ✅ Post-Deployment Verification
1. Open your Vercel URL.
2. Try to **Execute Analysis** for a ticker (e.g., AAPL).
3. Refresh the page to ensure the sidebar **History** persists.
4. Download a **PDF Report** to ensure the generator works.
