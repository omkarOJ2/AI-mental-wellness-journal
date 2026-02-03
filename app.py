from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import os
import json
from datetime import datetime, timedelta
import secrets
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

# Check mode: 'local' or 'cloud'
# Robust check: If running on Vercel, force cloud mode
IS_VERCEL = os.environ.get('VERCEL') == '1'
MODE = os.getenv('MODE', 'local').lower()

if IS_VERCEL:
    print("[INFO] Running on Vercel - Forcing CLOUD mode")
    MODE = 'cloud'

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Debug logging
print(f"[DEBUG] MODE: {MODE}")
print(f"[DEBUG] VERCEL detected: {IS_VERCEL}")
print(f"[DEBUG] SUPABASE_URL configured: {bool(SUPABASE_URL)}")
print(f"[DEBUG] SUPABASE_KEY configured: {bool(SUPABASE_KEY)}")

# Initialize clients based on mode
supabase = None
openai_client = None

if MODE == 'cloud':
    if not SUPABASE_URL or not SUPABASE_KEY:
        print(f"[ERROR] Missing Supabase configuration. URL: {bool(SUPABASE_URL)}, KEY: {bool(SUPABASE_KEY)}")
    else:
        try:
            from supabase import create_client, Client
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("[OK] Using Supabase (Cloud Mode)")
        except Exception as e:
            print(f"[ERROR] Supabase client creation failed: {e}")
            # On Vercel, we MUST stay in cloud mode to avoid SQLite permission errors
            if not IS_VERCEL:
                print("[INFO] Falling back to local mode")
                MODE = 'local'

# Always define database path for local mode
DATABASE = 'journal.db'

def get_db():
    """Get database connection"""
    # Ensure database file exists and is writable
    db_path = os.path.abspath(DATABASE)
    db = sqlite3.connect(db_path, check_same_thread=False)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize the database"""
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            sentiment_score REAL NOT NULL,
            emotions TEXT DEFAULT '[]',
            key_themes TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    db.commit()
    db.close()

# Initialize database ONLY in local mode
if MODE == 'local':
    print("[OK] Initializing SQLite (Local Mode)")
    init_db()
else:
    print("[OK] Skipping SQLite initialization in cloud mode")

# Initialize OpenAI if API key is available
if OPENAI_API_KEY and OPENAI_API_KEY.startswith('sk-'):
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print("[OK] Using GPT-4o for AI analysis")
    except Exception as e:
        print(f"[WARN] OpenAI initialization failed: {e}")
        openai_client = None


# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        try:
            if MODE == 'cloud' and supabase:
                # Try Supabase authentication first
                try:
                    auth_response = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })
                    
                    if auth_response.user:
                        session['access_token'] = auth_response.session.access_token
                        session['user'] = {
                            'id': auth_response.user.id,
                            'email': auth_response.user.email
                        }
                        return jsonify({'success': True, 'redirect': url_for('dashboard')})
                    else:
                        # If Supabase auth fails, try local SQLite
                        print("[DEBUG] Supabase auth failed, trying local SQLite")
                        raise Exception("Supabase auth failed")
                        
                except Exception as supabase_error:
                    # Fall back to local SQLite authentication ONLY if not on Vercel
                    if IS_VERCEL or MODE == 'cloud':
                        print(f"[ERROR] Supabase login failed: {supabase_error}")
                        return jsonify({'success': False, 'error': f'Cloud login failed: {str(supabase_error)}'}), 400
                    
                    print(f"[DEBUG] Supabase login failed: {supabase_error}, trying SQLite fallback")
                    pass  # Continue to SQLite check below
            
            # Local SQLite authentication
            if MODE == 'local':
                db = get_db()
                user = db.execute('SELECT * FROM users WHERE email = ? AND password = ?', 
                                (email, password)).fetchone()
                db.close()
                
                if user:
                    session['user'] = {
                        'id': user['id'],
                        'email': user['email']
                    }
                    return jsonify({'success': True, 'redirect': url_for('dashboard')})
            
            # If we get here, authentication failed
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 400
            
        except Exception as e:
            print(f"[ERROR] Login error: {e}")
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 400
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        use_fallback = False
        try:
            if MODE == 'cloud' and supabase:
                # Create user with Supabase Auth
                print(f"[DEBUG] Attempting Supabase signup for: {email}")
                try:
                    auth_response = supabase.auth.sign_up({
                        "email": email,
                        "password": password
                    })
                    
                    print(f"[DEBUG] Supabase response: {auth_response}")
                    
                    if auth_response.user:
                        # Check if email confirmation is required
                        if hasattr(auth_response, 'session') and auth_response.session is None:
                            return jsonify({
                                'success': True, 
                                'message': 'Account created! Please check your email to confirm your account before logging in.'
                            })
                        return jsonify({'success': True, 'message': 'Account created! Please log in.'})
                    else:
                        print(f"[ERROR] Supabase signup failed - no user returned")
                        return jsonify({'success': False, 'error': 'Failed to create account'}), 400
                        
                except Exception as supabase_error:
                    error_msg = str(supabase_error).lower()
                    # If rate limited, fall back to local SQLite
                    if 'rate limit' in error_msg or 'too many' in error_msg:
                        print(f"[WARN] Supabase rate limited, falling back to SQLite for this request")
                        use_fallback = True
                    else:
                        raise  # Re-raise if it's not a rate limit error
            
            # Local SQLite user creation
            if MODE == 'local':
                if IS_VERCEL:
                    missing_vars = []
                    if not SUPABASE_URL: missing_vars.append("SUPABASE_URL")
                    if not SUPABASE_KEY: missing_vars.append("SUPABASE_KEY")
                    
                    error_msg = "Database Unavailable on Vercel. "
                    if missing_vars:
                        error_msg += f"Missing Environment Variables: {', '.join(missing_vars)}. "
                    error_msg += "Please add them in Vercel Dashboard > Settings > Environment Variables."
                    
                    return jsonify({'success': False, 'error': error_msg}), 500
                
                db = None
                try:
                    db = get_db()
                    cursor = db.cursor()
                    cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)', 
                              (email, password))
                    db.commit()
                    
                    return jsonify({'success': True, 'message': 'Account created! Please log in.'})
                except sqlite3.IntegrityError:
                    if db:
                        db.rollback()
                    return jsonify({'success': False, 'error': 'Email already exists'}), 400
                except sqlite3.OperationalError as e:
                    if db:
                        db.rollback()
                    print(f"[ERROR] Database operational error: {e}")
                    return jsonify({'success': False, 'error': 'Database error. Vercel detected? Ensure MODE=cloud is set.'}), 500
                finally:
                    if db:
                        db.close()
            else:
                return jsonify({'success': False, 'error': 'Database not configured or unauthorized.'}), 500
        except Exception as e:
            error_message = str(e)
            print(f"[ERROR] Signup failed: {error_message}")
            print(f"[ERROR] Full exception: {repr(e)}")
            
            # Handle specific Supabase errors
            if 'rate limit' in error_message.lower() or 'too many requests' in error_message.lower():
                return jsonify({
                    'success': False, 
                    'error': 'Too many signup attempts. Please try again in a few minutes.'
                }), 429
            elif 'already registered' in error_message.lower() or 'already exists' in error_message.lower():
                return jsonify({'success': False, 'error': 'Email already exists'}), 400
            elif 'invalid email' in error_message.lower():
                return jsonify({'success': False, 'error': 'Invalid email address'}), 400
            elif 'password' in error_message.lower() and 'short' in error_message.lower():
                return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
            elif 'email' in error_message.lower() and 'confirm' in error_message.lower():
                return jsonify({
                    'success': False, 
                    'error': 'Please check your email to confirm your account'
                }), 400
            
            return jsonify({'success': False, 'error': error_message}), 400
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=session['user'])

@app.route('/api/journal/create', methods=['POST'])
@login_required
def create_journal_entry():
    data = request.get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    
    try:
        # Real GPT-4o sentiment analysis (The "Brain")
        sentiment_analysis = analyze_sentiment_gpt4o(content)
        
        # Insert into Supabase with RLS (The "Vault")
        user_id = session['user']['id']
        
        entry_data = {
            'user_id': user_id,
            'content': content,
            'sentiment_score': sentiment_analysis['sentiment_score'],
            'emotions': sentiment_analysis['emotions'],
            'key_themes': sentiment_analysis['key_themes']
        }
        
        result = supabase.table('journal_entries').insert(entry_data).execute()
        
        if result.data:
            return jsonify({
                'success': True,
                'entry': result.data[0],
                'analysis': sentiment_analysis
            })
        else:
            return jsonify({'error': 'Failed to create entry'}), 500
            
    except Exception as e:
        print(f"Create Entry Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/journal/update/<entry_id>', methods=['PUT'])
@login_required
def update_journal_entry(entry_id):
    data = request.get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    
    try:
        # Re-analyze sentiment with GPT-4o
        sentiment_analysis = analyze_sentiment_gpt4o(content)
        
        user_id = session['user']['id']
        
        # Update with Supabase (RLS ensures user can only update their own entries)
        update_data = {
            'content': content,
            'sentiment_score': sentiment_analysis['sentiment_score'],
            'emotions': sentiment_analysis['emotions'],
            'key_themes': sentiment_analysis['key_themes']
        }
        
        result = supabase.table('journal_entries')\
            .update(update_data)\
            .eq('id', entry_id)\
            .eq('user_id', user_id)\
            .execute()
        
        if result.data:
            return jsonify({
                'success': True,
                'entry': result.data[0],
                'analysis': sentiment_analysis
            })
        else:
            return jsonify({'error': 'Entry not found or unauthorized'}), 404
            
    except Exception as e:
        print(f"Update Entry Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/journal/delete/<entry_id>', methods=['DELETE'])
@login_required
def delete_journal_entry(entry_id):
    try:
        user_id = session['user']['id']
        
        # Delete with Supabase (RLS ensures user can only delete their own entries)
        result = supabase.table('journal_entries')\
            .delete()\
            .eq('id', entry_id)\
            .eq('user_id', user_id)\
            .execute()
        
        if result.data:
            return jsonify({
                'success': True,
                'message': 'Entry deleted successfully'
            })
        else:
            return jsonify({'error': 'Entry not found or unauthorized'}), 404
            
    except Exception as e:
        print(f"Delete Entry Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/journal/search', methods=['GET'])
@login_required
def search_journal_entries():
    try:
        user_id = session['user']['id']
        query = request.args.get('q', '')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sentiment = request.args.get('sentiment')  # 'positive', 'neutral', 'negative'
        
        # Build Supabase query (RLS automatically filters by user_id)
        query_builder = supabase.table('journal_entries').select('*').eq('user_id', user_id)
        
        # Add search term
        if query:
            query_builder = query_builder.ilike('content', f'%{query}%')
        
        # Add date range
        if start_date:
            query_builder = query_builder.gte('created_at', start_date)
        
        if end_date:
            query_builder = query_builder.lte('created_at', end_date)
        
        # Add sentiment filter
        if sentiment == 'positive':
            query_builder = query_builder.gt('sentiment_score', 0.3)
        elif sentiment == 'negative':
            query_builder = query_builder.lt('sentiment_score', -0.3)
        elif sentiment == 'neutral':
            query_builder = query_builder.gte('sentiment_score', -0.3).lte('sentiment_score', 0.3)
        
        result = query_builder.order('created_at', desc=True).execute()
        
        return jsonify({
            'entries': result.data,
            'count': len(result.data)
        })
    except Exception as e:
        print(f"Search Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/journal/entries', methods=['GET'])
@login_required
def get_journal_entries():
    try:
        user_id = session['user']['id']
        
        # Get entries for the last 30 days from Supabase
        thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
        
        result = supabase.table('journal_entries')\
            .select('*')\
            .eq('user_id', user_id)\
            .gte('created_at', thirty_days_ago)\
            .order('created_at', desc=True)\
            .execute()
        
        return jsonify({'entries': result.data})
    except Exception as e:
        print(f"Get Entries Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/weekly-report', methods=['GET'])
@login_required
def get_weekly_report():
    try:
        user_id = session['user']['id']
        
        # Get entries from the last 7 days from Supabase
        seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        result = supabase.table('journal_entries')\
            .select('*')\
            .eq('user_id', user_id)\
            .gte('created_at', seven_days_ago)\
            .order('created_at', desc=False)\
            .execute()
        
        if not result.data:
            return jsonify({'report': None, 'message': 'No entries found for the last week'})
        
        # Generate AI-powered report with GPT-4o
        report = generate_weekly_report_gpt4o(result.data)
        
        return jsonify({'report': report})
    except Exception as e:
        print(f"Weekly Report Error: {e}")
        return jsonify({'error': str(e)}), 500

def analyze_sentiment_gpt4o(text):
    """
    Real GPT-4o sentiment analysis (The "Brain")
    Performs nuanced emotional analysis beyond simple positive/negative labels
    """
    try:
        prompt = f"""Analyze the following journal entry for emotional content and themes.
Provide a detailed psychological analysis with:
1. Sentiment score (-1.0 to 1.0, where -1 is very negative, 0 is neutral, 1 is very positive)
2. Up to 3 primary emotions detected (e.g., anxious, grateful, stressed, hopeful, etc.)
3. Up to 2 key themes (e.g., work, relationships, health, personal growth, etc.)
4. A brief empathetic insight (1-2 sentences)

Journal Entry:
"{text}"

Respond ONLY with valid JSON in this exact format:
{{
    "sentiment_score": 0.5,
    "emotions": ["emotion1", "emotion2", "emotion3"],
    "key_themes": ["theme1", "theme2"],
    "brief_insight": "Your insight here"
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an empathetic mental wellness AI assistant specializing in emotional analysis. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        # Parse the JSON response
        result = json.loads(response.choices[0].message.content)
        
        # Validate and ensure proper format
        return {
            'sentiment_score': float(result.get('sentiment_score', 0.0)),
            'emotions': result.get('emotions', ['neutral'])[:3],
            'key_themes': result.get('key_themes', ['self-reflection'])[:2],
            'brief_insight': result.get('brief_insight', 'Your entry has been analyzed.')
        }
    
    except Exception as e:
        print(f"GPT-4o Analysis Error: {e}")
        # Fallback to basic analysis if API fails
        return {
            'sentiment_score': 0.0,
            'emotions': ['reflective'],
            'key_themes': ['self-reflection'],
            'brief_insight': 'Your entry has been recorded. AI analysis temporarily unavailable.'
        }

def generate_weekly_report_gpt4o(entries):
    """
    Generate AI-powered weekly report with activity-mood correlation (The "Brain")
    Uses GPT-4o to synthesize insights and identify patterns
    """
    try:
        # Calculate basic statistics
        sentiments = [entry['sentiment_score'] for entry in entries]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        best_entry = max(entries, key=lambda x: x['sentiment_score'])
        worst_entry = min(entries, key=lambda x: x['sentiment_score'])
        
        # Prepare entries summary for GPT-4o
        entries_summary = []
        for entry in entries:
            emotions = json.loads(entry['emotions']) if isinstance(entry['emotions'], str) else entry['emotions']
            themes = json.loads(entry['key_themes']) if isinstance(entry['key_themes'], str) else entry['key_themes']
            entries_summary.append({
                'date': entry['created_at'][:10],
                'sentiment': entry['sentiment_score'],
                'emotions': emotions,
                'themes': themes,
                'preview': entry['content'][:200]
            })
        
        prompt = f"""As an empathetic mental wellness AI, analyze this week's journal entries and provide insights.

Week Summary:
- Total entries: {len(entries)}
- Average sentiment: {avg_sentiment:.2f}
- Best day: {best_entry['created_at'][:10]} (score: {best_entry['sentiment_score']:.2f})
- Challenging day: {worst_entry['created_at'][:10]} (score: {worst_entry['sentiment_score']:.2f})

Entries:
{json.dumps(entries_summary, indent=2)}

Provide a comprehensive weekly analysis with:
1. Overall mood assessment (one word: Positive/Balanced/Challenging)
2. Emotional trajectory (brief phrase)
3. 3-5 key insights about patterns, triggers, or correlations between activities and mood
4. 3 personalized recommendations for next week

Respond ONLY with valid JSON:
{{
    "overall_mood": "Positive",
    "trajectory": "Upward trend",
    "key_insights": ["insight1", "insight2", "insight3"],
    "recommendations": ["rec1", "rec2", "rec3"]
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a compassionate mental wellness AI that helps users understand their emotional patterns. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=500
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Calculate mood distribution
        positive_count = sum(1 for s in sentiments if s > 0.3)
        negative_count = sum(1 for s in sentiments if s < -0.3)
        neutral_count = len(sentiments) - positive_count - negative_count
        
        return {
            'overall_mood': result.get('overall_mood', 'Balanced'),
            'trajectory': result.get('trajectory', 'Stable'),
            'key_insights': result.get('key_insights', [f'You created {len(entries)} journal entries this week']),
            'recommendations': result.get('recommendations', ['Continue your daily journaling practice']),
            'sentiment_graph': sentiments,
            'best_day': {
                'date': best_entry['created_at'][:10],
                'score': best_entry['sentiment_score'],
                'content_preview': best_entry['content'][:100] + '...' if len(best_entry['content']) > 100 else best_entry['content']
            },
            'worst_day': {
                'date': worst_entry['created_at'][:10],
                'score': worst_entry['sentiment_score'],
                'content_preview': worst_entry['content'][:100] + '...' if len(worst_entry['content']) > 100 else worst_entry['content']
            },
            'mood_distribution': {
                'positive': positive_count,
                'neutral': neutral_count,
                'negative': negative_count
            }
        }
    
    except Exception as e:
        print(f"GPT-4o Weekly Report Error: {e}")
        # Fallback to basic report
        sentiments = [entry['sentiment_score'] for entry in entries]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        return {
            'overall_mood': 'Balanced',
            'trajectory': 'Stable',
            'key_insights': [f'You created {len(entries)} journal entries this week'],
            'recommendations': ['Continue your daily journaling practice'],
            'sentiment_graph': sentiments,
            'best_day': {'date': entries[0]['created_at'][:10], 'score': 0, 'content_preview': ''},
            'worst_day': {'date': entries[0]['created_at'][:10], 'score': 0, 'content_preview': ''},
            'mood_distribution': {'positive': 0, 'neutral': len(entries), 'negative': 0}
        }

@app.route('/api/export/json', methods=['GET'])
@login_required
def export_json():
    """Export all journal entries as JSON"""
    try:
        user_id = session['user']['id']
        
        # Get all entries for user from Supabase
        result = supabase.table('journal_entries')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()
        
        export_data = {
            'user_email': session['user']['email'],
            'export_date': datetime.utcnow().isoformat(),
            'total_entries': len(result.data),
            'entries': result.data
        }
        
        response = jsonify(export_data)
        response.headers['Content-Disposition'] = f'attachment; filename=journal_export_{datetime.now().strftime("%Y%m%d")}.json'
        return response
        
    except Exception as e:
        print(f"Export JSON Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/draft/save', methods=['POST'])
@login_required
def save_draft():
    """Auto-save draft (using browser localStorage instead of database)"""
    # Note: Drafts are now handled client-side with localStorage
    # This endpoint kept for backwards compatibility
    return jsonify({'success': True, 'message': 'Draft saved locally'})

@app.route('/api/draft/load', methods=['GET'])
@login_required
def load_draft():
    """Load saved draft (using browser localStorage)"""
    # Note: Drafts are now handled client-side
    return jsonify({'content': None})

@app.route('/api/draft/clear', methods=['DELETE'])
@login_required
def clear_draft():
    """Clear saved draft (using browser localStorage)"""
    # Note: Drafts are now handled client-side
    return jsonify({'success': True})

@app.route('/api/weekly-comparison', methods=['GET'])
@login_required
def get_weekly_comparison():
    """Get week-over-week comparison"""
    try:
        user_id = session['user']['id']
        
        # Get this week's entries
        this_week_start = (datetime.utcnow() - timedelta(days=7)).isoformat()
        this_week_result = supabase.table('journal_entries')\
            .select('*')\
            .eq('user_id', user_id)\
            .gte('created_at', this_week_start)\
            .order('created_at', desc=False)\
            .execute()
        
        # Get last week's entries
        last_week_start = (datetime.utcnow() - timedelta(days=14)).isoformat()
        last_week_end = this_week_start
        last_week_result = supabase.table('journal_entries')\
            .select('*')\
            .eq('user_id', user_id)\
            .gte('created_at', last_week_start)\
            .lt('created_at', last_week_end)\
            .order('created_at', desc=False)\
            .execute()
        
        # Calculate averages
        this_week = this_week_result.data
        last_week = last_week_result.data
        
        this_week_avg = sum(e['sentiment_score'] for e in this_week) / len(this_week) if this_week else 0
        last_week_avg = sum(e['sentiment_score'] for e in last_week) / len(last_week) if last_week else 0
        
        change = this_week_avg - last_week_avg
        change_percent = (change / abs(last_week_avg) * 100) if last_week_avg != 0 else 0
        
        return jsonify({
            'this_week': {
                'avg_sentiment': round(this_week_avg, 2),
                'entry_count': len(this_week)
            },
            'last_week': {
                'avg_sentiment': round(last_week_avg, 2),
                'entry_count': len(last_week)
            },
            'change': round(change, 2),
            'change_percent': round(change_percent, 1),
            'trend': 'improving' if change > 0 else 'declining' if change < 0 else 'stable'
        })
    except Exception as e:
        print(f"Weekly Comparison Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/pdf', methods=['GET'])
@login_required
def export_pdf():
    """Export journal as text file"""
    try:
        from flask import make_response
        
        user_id = session['user']['id']
        
        result = supabase.table('journal_entries')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()
        
        # Create text-based export content
        pdf_content = f"""SENTIENT JOURNAL - EXPORT
User: {session['user']['email']}
Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Entries: {len(result.data)}

{'='*80}

"""
        
        for entry in result.data:
            emotions = entry.get('emotions', [])
            themes = entry.get('key_themes', [])
            
            pdf_content += f"""
Date: {entry['created_at']}
Sentiment Score: {entry['sentiment_score']:.2f}
Emotions: {', '.join(emotions)}
Themes: {', '.join(themes)}

{entry['content']}

{'-'*80}

"""
        
        # Return as downloadable text file
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=journal_export_{datetime.now().strftime("%Y%m%d")}.txt'
        
        return response
        
    except Exception as e:
        print(f"Export PDF Error: {e}")
        return jsonify({'error': str(e)}), 500

# ========================================
# WELLNESS ASSISTANT CHAT API
# ========================================

@app.route('/api/chat/reflect', methods=['POST'])
@login_required
def chat_reflect():
    """Intelligent Wellness Assistant that helps users with journaling and mental wellness"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').lower().strip()
        user_id = session['user']['id']
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get user's journal data for context
        db = get_db()
        
        # Get recent entries
        recent_entries = db.execute('''
            SELECT * FROM journal_entries 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 10
        ''', (user_id,)).fetchall()
        
        # Get total entry count
        total_entries = db.execute('''
            SELECT COUNT(*) as count FROM journal_entries WHERE user_id = ?
        ''', (user_id,)).fetchone()['count']
        
        # Calculate average sentiment
        avg_sentiment = 0
        if recent_entries:
            sentiments = [entry['sentiment_score'] for entry in recent_entries]
            avg_sentiment = sum(sentiments) / len(sentiments)
        
        db.close()
        
        # Generate intelligent response based on user message
        reply, suggested_prompts = generate_assistant_response(
            user_message, 
            total_entries, 
            avg_sentiment, 
            recent_entries
        )
        
        return jsonify({
            'reply': reply,
            'suggested_prompts': suggested_prompts
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_assistant_response(message, total_entries, avg_sentiment, recent_entries):
    """Generate contextual responses based on user queries"""
    
    # Greeting responses
    if any(word in message for word in ['hello', 'hi', 'hey', 'greetings']):
        if total_entries == 0:
            return (
                "👋 Hello! I'm your Wellness Assistant. I'm here to help you start your mental wellness journey through journaling. "
                "Would you like some tips on how to begin?",
                ["How do I start journaling?", "What should I write about?", "Show me journaling tips"]
            )
        else:
            mood_desc = "positive" if avg_sentiment > 0.3 else "challenging" if avg_sentiment < -0.3 else "balanced"
            return (
                f"👋 Welcome back! You've written {total_entries} journal entries so far. "
                f"Your recent mood has been {mood_desc}. How can I help you today?",
                ["Show my progress", "Give me journaling tips", "Help me reflect on patterns"]
            )
    
    # Progress and stats queries
    elif any(word in message for word in ['progress', 'stats', 'how am i doing', 'track']):
        if total_entries == 0:
            return (
                "You haven't started journaling yet! Let's begin your wellness journey. "
                "Regular journaling helps you track emotions, identify patterns, and improve mental health.",
                ["Start my first entry", "Why should I journal?", "What are the benefits?"]
            )
        else:
            mood_emoji = "😊" if avg_sentiment > 0.3 else "😔" if avg_sentiment < -0.3 else "😐"
            return (
                f"{mood_emoji} You've written {total_entries} journal entries! "
                f"Your average emotional state is {avg_sentiment:.2f}. "
                f"{'Keep up the great work!' if avg_sentiment > 0 else 'Remember, tough times are temporary. Keep journaling to track your journey.'} "
                f"Consistency is key to mental wellness!",
                ["Show weekly report", "View emotional trends", "Compare this week vs last week"]
            )
    
    # Journaling tips and how-to
    elif any(word in message for word in ['how', 'start', 'begin', 'tips', 'help', 'guide']):
        return (
            "📝 Here are some powerful journaling tips:\n\n"
            "1. **Be Honest**: Write freely without judgment\n"
            "2. **Be Specific**: Include details about your day and feelings\n"
            "3. **Be Consistent**: Try to journal daily, even if brief\n"
            "4. **Reflect**: Ask yourself 'What did I learn today?'\n"
            "5. **Express Gratitude**: Note 3 things you're grateful for\n\n"
            "Ready to write your next entry?",
            ["Start writing now", "Tell me more about consistency", "What should I write about?"]
        )
    
    # What to write about
    elif any(word in message for word in ['write about', 'topics', 'ideas', 'prompts']):
        return (
            "💡 Great journaling prompts:\n\n"
            "• How are you feeling right now and why?\n"
            "• What challenged you today and how did you handle it?\n"
            "• What made you smile or feel grateful?\n"
            "• What patterns do you notice in your emotions?\n"
            "• What goals do you want to work towards?\n"
            "• Who or what inspired you recently?\n\n"
            "Pick one and start writing!",
            ["I'll start writing", "Give me more prompts", "Show my recent entries"]
        )
    
    # Mental wellness and self-care
    elif any(word in message for word in ['wellness', 'mental health', 'self-care', 'anxiety', 'stress', 'depressed']):
        return (
            "🧠 Mental wellness is a journey, not a destination. Here's what can help:\n\n"
            "• **Journal regularly** to process emotions\n"
            "• **Practice mindfulness** and deep breathing\n"
            "• **Stay connected** with supportive people\n"
            "• **Move your body** - exercise helps mood\n"
            "• **Sleep well** - rest is crucial\n"
            "• **Seek help** when needed - it's a sign of strength\n\n"
            "Remember: You're not alone in this journey. 💚",
            ["Track my mood patterns", "I want to journal now", "Show my progress"]
        )
    
    # Consistency and habits
    elif any(word in message for word in ['consistent', 'habit', 'daily', 'routine', 'streak']):
        return (
            "🔥 Building a journaling habit:\n\n"
            "• **Set a specific time** - morning or before bed works great\n"
            "• **Start small** - even 5 minutes counts\n"
            "• **Use reminders** - set a daily alarm\n"
            "• **Track your streak** - celebrate small wins\n"
            "• **Don't break the chain** - write something every day\n\n"
            f"You've written {total_entries} entries so far. Keep going!",
            ["Write my entry now", "Show my streak", "Give me motivation"]
        )
    
    # Patterns and insights
    elif any(word in message for word in ['pattern', 'insight', 'trend', 'notice', 'learn']):
        if total_entries < 5:
            return (
                "To identify meaningful patterns, try journaling for at least a week. "
                "The more you write, the clearer your emotional patterns become!",
                ["Start writing more", "What should I track?", "Show journaling tips"]
            )
        else:
            return (
                f"📊 Based on your {total_entries} entries, here's what I notice:\n\n"
                f"• Your average mood is {avg_sentiment:.2f}\n"
                f"• {'You tend to be optimistic!' if avg_sentiment > 0.3 else 'You face challenges with resilience.' if avg_sentiment < -0.3 else 'Your emotions are balanced.'}\n"
                "• Check your Emotional Trends tab for visual insights\n"
                "• Review your Weekly Report for detailed analysis\n\n"
                "Keep journaling to discover more patterns!",
                ["View emotional trends", "Generate weekly report", "Continue journaling"]
            )
    
    # Motivation and encouragement
    elif any(word in message for word in ['motivate', 'encourage', 'inspire', 'why journal']):
        return (
            "✨ Why journaling is powerful:\n\n"
            "• **Clarity**: Untangle complex emotions\n"
            "• **Growth**: Track your personal evolution\n"
            "• **Healing**: Process difficult experiences\n"
            "• **Gratitude**: Focus on positive moments\n"
            "• **Self-awareness**: Understand yourself better\n"
            "• **Stress relief**: Release pent-up feelings\n\n"
            "You're investing in yourself. That's beautiful! 💪",
            ["I'm ready to write", "Show my progress", "Give me writing prompts"]
        )
    
    # Weekly report
    elif any(word in message for word in ['week', 'report', 'summary']):
        return (
            "📊 To see your weekly insights:\n\n"
            "1. Click on the **Weekly Report** tab\n"
            "2. Press **Generate Weekly Insights**\n"
            "3. Review your mood trends, best/worst days, and recommendations\n\n"
            "Your weekly report helps you understand your emotional journey!",
            ["Take me to reports", "Show my trends", "I'll write more entries"]
        )
    
    # Export data
    elif any(word in message for word in ['export', 'download', 'backup', 'save']):
        return (
            "💾 To export your journal:\n\n"
            "1. Go to the **Export Data** tab\n"
            "2. Choose **JSON** (for data) or **Text** (for reading)\n"
            "3. Your entries will download automatically\n\n"
            "It's always good to backup your thoughts!",
            ["Show export options", "Continue journaling", "View my entries"]
        )
    
    # Default helpful response
    else:
        return (
            "I'm here to help you with:\n\n"
            "• **Journaling tips** and writing prompts\n"
            "• **Progress tracking** and emotional insights\n"
            "• **Mental wellness** guidance and support\n"
            "• **Building habits** and staying consistent\n\n"
            "What would you like to explore?",
            ["Give me journaling tips", "Show my progress", "Help me stay consistent", "What should I write about?"]
        )


if __name__ == '__main__':
    print("\n" + "="*60)
    print("AI Mental Wellness Journal - Vibe Coding Edition")
    print("="*60)
    print("Running on: http://localhost:5000")
    print("Using Supabase + GPT-4o + RLS Security")
    print("\nCreate an account and start journaling!")
    print("="*60 + "\n")
    app.run(debug=True, port=5000)
