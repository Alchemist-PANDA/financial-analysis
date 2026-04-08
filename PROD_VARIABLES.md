# 📋 Production Environment Variables Cheat-Sheet

Use this guide when setting up your apps on **Render** and **Vercel**.

---

## 🐍 1. For Render (Backend)
Add these in **Dashboard > Advanced > Environment Variables**:

| Key | Value | Notes |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgres://user:pass@ep-pool...` | From Neon.tech |
| `GROQ_API_KEY` | `gsk_...` | From Groq |
| `TAVILY_API_KEY` | `tvly-...` | From Tavily |
| `API_SECRET_KEY` | `a_strong_random_token` | **Shared Secret** |
| `FRONTEND_URL` | `https://your-app.vercel.app` | From Vercel (add after Vercel setup) |
| `RENDER` | `true` | Helps the app identify it's in prod |

---

## ⚛️ 2. For Vercel (Frontend)
Add these in **Project Settings > Environment Variables**:

| Key | Value | Notes |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | `https://xxx.onrender.com` | From Render |
| `NEXT_PUBLIC_API_KEY` | `a_strong_random_token` | **Must Match Backend Key** |

---

## 🔒 Security Note
> [!IMPORTANT]
> The `API_SECRET_KEY` and `NEXT_PUBLIC_API_KEY` **must be identical**. This prevents unauthorized users from calling your analysis engine and draining your API quotas.
