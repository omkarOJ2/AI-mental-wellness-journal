"""Quick test to check Supabase connection"""
import os
from dotenv import load_dotenv

load_dotenv()

print("Testing Supabase connection...")
print(f"URL: {os.getenv('SUPABASE_URL')}")
print(f"Key: {os.getenv('SUPABASE_KEY')[:20]}...")

try:
    from supabase import create_client
    
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )
    
    # Try a simple query
    result = supabase.table('journal_entries').select('*').limit(1).execute()
    print("\n✅ SUCCESS! Supabase connection works!")
    print(f"Connected to: {os.getenv('SUPABASE_URL')}")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\nPossible issues:")
    print("1. Check your internet connection")
    print("2. Verify Supabase URL and Key are correct")
    print("3. Make sure you ran database/setup.sql in Supabase")
