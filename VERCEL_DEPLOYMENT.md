# 🚀 Vercel Deployment Guide

Follow these steps to deploy your AI Mental Wellness Journal to Vercel.

## 1. Environment Variables

You must configure the following environment variables in the Vercel Dashboard (Settings > Environment Variables):

| Variable | Value | Description |
|----------|-------|-------------|
| **`MODE`** | **`cloud`** | **OPTIONAL BUT RECOMMENDED**: The app now auto-detects Vercel and forces cloud mode safely. |
| `SUPABASE_URL` | `https://your-project.supabase.co` | Your Supabase Project URL |
| `SUPABASE_KEY` | `your-anon-key` | Your Supabase Anon/Public Key |
| `OPENAI_API_KEY` | `sk-...` | Your OpenAI API Key |
| `FLASK_SECRET_KEY` | `your-random-string` | A secure random string for sessions |
| **`VERCEL`** | **`1`** | **DO NOT REMOVE**: Vercel sets this automatically; the app uses it to disable SQLite. |

## 2. Deployment Steps

### Option A: Via Vercel Dashboard (Recommended)
1. Push your code to a GitHub repository.
2. Go to [vercel.com/new](https://vercel.com/new).
3. Import your repository.
4. In the "Configure Project" step:
   - Ensure the **Framework Preset** is set to "Other".
   - Under **Environment Variables**, add the variables listed above.
5. Click **Deploy**.

### Option B: Via Vercel CLI
1. Install Vercel CLI: `npm install -g vercel`
2. Run `vercel` in the project root.
3. Follow the prompts to link your account.
4. Set the environment variables using `vercel env add`.
5. Run `vercel --prod` to deploy.

## 3. Database Setup

Ensure you have run the `database/setup.sql` script in your Supabase SQL Editor to create the necessary tables and RLS policies.

---
*Note: Vercel uses a read-only filesystem. SQLite will not work on Vercel, which is why `MODE=cloud` is required to use Supabase instead.*
