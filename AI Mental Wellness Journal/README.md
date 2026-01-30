# AI Mental Wellness Journal

A Flask-based mental wellness journaling application with AI-powered sentiment analysis and weekly emotional trend reports.

## Features

- 🔐 **User Authentication** - Secure signup/login with Supabase
- ✍️ **Journal Entries** - Write and save daily reflections
- 🧠 **AI Sentiment Analysis** - GPT-4o analyzes emotions and themes
- 📊 **Weekly Reports** - AI-generated emotional trend insights
- 🎨 **Beautiful UI** - Modern, gradient-based design

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: Supabase (PostgreSQL)
- **AI**: OpenAI GPT-4o
- **Frontend**: HTML, CSS, JavaScript

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- Supabase account
- OpenAI API key

### 2. Installation

```bash
# Clone or navigate to the project directory
cd "e:\AI Mental Wellness Journal"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
FLASK_SECRET_KEY=your-secret-key-here
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-anon-key
OPENAI_API_KEY=your-openai-api-key
```

### 4. Supabase Database Setup

Create a `journal_entries` table in your Supabase database:

```sql
CREATE TABLE journal_entries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sentiment_score FLOAT,
    emotions TEXT[],
    key_themes TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;

-- Create policy for users to only see their own entries
CREATE POLICY "Users can view their own entries"
    ON journal_entries FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own entries"
    ON journal_entries FOR INSERT
    WITH CHECK (auth.uid() = user_id);
```

### 5. Run the Application

```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

## Usage

1. **Sign Up**: Create a new account
2. **Login**: Access your dashboard
3. **Write**: Create journal entries
4. **Analyze**: View AI sentiment analysis
5. **Review**: Generate weekly wellness reports

## Project Structure

```
AI Mental Wellness Journal/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules
├── templates/
│   ├── login.html        # Login page
│   ├── signup.html       # Signup page
│   └── dashboard.html    # Main dashboard
└── README.md             # This file
```

## Security Notes

- Never commit `.env` file to version control
- Use strong passwords for user accounts
- Keep API keys confidential
- Enable Supabase RLS policies for data security

## License

MIT License - feel free to use for personal or commercial projects.
