# 🚀 Supabase Setup - Step-by-Step Guide

## Step 1: Create Supabase Account & Project (5 minutes)

### 1.1 Sign Up for Supabase
1. Open your browser and go to: **https://supabase.com**
2. Click **"Start your project"** or **"Sign in"**
3. Sign up with GitHub (recommended) or email
4. Verify your email if required

### 1.2 Create New Project
1. Once logged in, click **"New Project"**
2. Fill in the details:
   - **Name**: `ai-mental-wellness-journal` (or any name you prefer)
   - **Database Password**: Create a strong password (save it somewhere safe!)
   - **Region**: Choose closest to you (e.g., `us-east-1`)
   - **Pricing Plan**: Select **"Free"** (perfect for this project)
3. Click **"Create new project"**
4. Wait 2-3 minutes for project to initialize

---

## Step 2: Get Your API Credentials (2 minutes)

### 2.1 Navigate to API Settings
1. In your Supabase project dashboard, click **"Settings"** (gear icon) in the left sidebar
2. Click **"API"** under Project Settings

### 2.2 Copy Your Credentials
You'll see two important values:

**Project URL:**
```
https://xxxxxxxxxxxxx.supabase.co
```

**anon/public key:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS...
```

### 2.3 Update Your .env File
1. Open `e:\AI Mental Wellness Journal\.env` in your editor
2. Replace the placeholder values:

```env
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

3. Save the file

---

## Step 3: Run Database Setup Script (3 minutes)

### 3.1 Open SQL Editor
1. In Supabase dashboard, click **"SQL Editor"** in left sidebar
2. Click **"New query"** button

### 3.2 Copy & Execute Setup Script
1. Open `e:\AI Mental Wellness Journal\database\setup.sql` in your editor
2. **Copy ALL the contents** (lines 1-88)
3. **Paste** into the Supabase SQL Editor
4. Click **"Run"** button (or press Ctrl+Enter)

### 3.3 Verify Success
You should see:
- ✅ "Success. No rows returned"
- This means the table and RLS policies were created successfully

---

## Step 4: Verify Database Setup (2 minutes)

### 4.1 Check Table Creation
1. In Supabase, click **"Table Editor"** in left sidebar
2. You should see a table named **`journal_entries`**
3. Click on it to see the columns:
   - `id` (uuid)
   - `user_id` (uuid)
   - `content` (text)
   - `sentiment_score` (numeric)
   - `emotions` (jsonb)
   - `key_themes` (jsonb)
   - `created_at` (timestamp)
   - `updated_at` (timestamp)

### 4.2 Verify RLS is Enabled
1. Still in Table Editor, look at the top of the page
2. You should see: **"RLS enabled"** with a green checkmark
3. Click **"View policies"** to see all 4 policies:
   - Users can view their own entries
   - Users can insert their own entries
   - Users can update their own entries
   - Users can delete their own entries

---

## Step 5: Enable Email Authentication (1 minute)

### 5.1 Configure Auth Settings
1. Click **"Authentication"** in left sidebar
2. Click **"Providers"** tab
3. Make sure **"Email"** is enabled (it should be by default)
4. Optional: Disable email confirmation for testing
   - Click **"Settings"** under Authentication
   - Scroll to "Email Auth"
   - Toggle **"Enable email confirmations"** to OFF (for easier testing)
   - Click **"Save"**

---

## ✅ Supabase Setup Complete!

Your Supabase project is now ready. You should have:
- ✅ Project created
- ✅ API credentials in `.env` file
- ✅ Database table created
- ✅ RLS policies enforced
- ✅ Email authentication enabled

---

## Next Step: Run the Application

Once you've completed all steps above, you're ready to run the app!

```bash
python app.py
```

Then visit: **http://localhost:5000**

---

## Troubleshooting

### "Table already exists" error
- This is fine! It means the table was created successfully
- The script uses `CREATE TABLE IF NOT EXISTS`

### Can't find API credentials
- Go to: Settings → API
- Look for "Project URL" and "Project API keys"
- Use the **anon/public** key, NOT the service_role key

### RLS not showing as enabled
- Go to Table Editor → journal_entries
- Click the shield icon to enable RLS
- Re-run the SQL script to create policies

---

**Ready to proceed? Let me know when you've completed these steps!**
