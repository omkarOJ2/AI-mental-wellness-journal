# 🚀 Quick Setup Guide - AI Mental Wellness Journal

## Prerequisites
- Python 3.8+
- Supabase account (free tier works)
- OpenAI API key (GPT-4o access)

## Step 1: Clone & Install Dependencies

```bash
cd "e:\AI Mental Wellness Journal"
pip install -r requirements.txt
```

## Step 2: Set Up Supabase (The "Foundation" + "Vault")

1. **Create Supabase Project**
   - Go to https://supabase.com
   - Click "New Project"
   - Note your project URL and anon key

2. **Run Database Setup**
   - Open Supabase SQL Editor
   - Copy contents from `database/setup.sql`
   - Execute the script
   - This creates the `journal_entries` table with RLS policies

3. **Verify RLS is Enabled**
   - Go to Database > Tables > journal_entries
   - Check that "Enable RLS" is ON
   - Verify 4 policies exist (SELECT, INSERT, UPDATE, DELETE)

## Step 3: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and fill in:
   ```env
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   OPENAI_API_KEY=sk-your-openai-api-key
   ```

## Step 4: Run the Application

```bash
python app.py
```

Visit: http://localhost:5000

## Step 5: Test the Features

### Test Authentication
1. Sign up with a new email/password
2. Log in with those credentials
3. Verify you're redirected to dashboard

### Test AI Sentiment Analysis (The "Brain")
1. Create a journal entry: "I'm feeling grateful and happy today!"
2. Check that GPT-4o analyzes emotions and themes
3. Verify sentiment score appears

### Test Voice Input
1. Click "Voice Input" button
2. Speak your journal entry
3. Verify text appears in textarea

### Test Writing Prompts
1. Click different prompt categories
2. Click "Use This Prompt"
3. Verify prompt appears in journal textarea

### Test Weekly Report
1. Create 3-5 entries over different days
2. Navigate to Weekly Report section
3. Verify GPT-4o generates insights with activity correlations

### Test RLS (The "Vault")
1. Create entries with User A
2. Log out and create User B
3. Verify User B cannot see User A's entries

## Troubleshooting

### "Supabase connection failed"
- Check SUPABASE_URL and SUPABASE_KEY in .env
- Verify you ran database/setup.sql
- Check Supabase project is active

### "OpenAI API error"
- Verify OPENAI_API_KEY is correct
- Check you have GPT-4o access
- Ensure you have API credits

### "Voice input not working"
- Use Chrome or Edge browser
- Allow microphone permissions
- Check browser console for errors

## Success Criteria ✅

Your implementation is complete when:
- ✅ Supabase authentication works
- ✅ RLS prevents cross-user data access
- ✅ GPT-4o provides real sentiment analysis
- ✅ Weekly reports show AI-generated insights
- ✅ Voice input transcribes speech to text
- ✅ Writing prompts help overcome writer's block

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│           USER INTERFACE (Zero-Friction)     │
│  - Voice Input (Web Speech API)             │
│  - Writing Prompts (5 Categories)           │
│  - Natural Language Journaling              │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         FLASK BACKEND (Orchestration)        │
│  - Supabase Auth (JWT Tokens)               │
│  - API Routes                                │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌───────▼────────┐
│   SUPABASE     │   │    GPT-4o      │
│  (Foundation)  │   │    (Brain)     │
│  - PostgreSQL  │   │  - Sentiment   │
│  - RLS (Vault) │   │  - Reports     │
│  - Auth        │   │  - Correlation │
└────────────────┘   └────────────────┘
```

## Next Steps

1. **Customize Prompts**: Edit `static/js/writing-prompts.js`
2. **Add More Features**: Habit tracking, calendar view, streaks
3. **Deploy**: Use Vercel, Railway, or Heroku
4. **Monitor**: Check Supabase dashboard for usage

---

**Congratulations! Your AI Mental Wellness Journal is now fully aligned with the Vibe Coding methodology! 🎉**
