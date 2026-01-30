"""
Validation Script for AI Mental Wellness Journal
Tests all critical components of the Vibe Coding implementation
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def validate_environment():
    """Validate environment variables are set"""
    print("🔍 Validating Environment Variables...")
    
    required_vars = {
        'SUPABASE_URL': os.getenv('SUPABASE_URL'),
        'SUPABASE_KEY': os.getenv('SUPABASE_KEY'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
    }
    
    missing = []
    for var, value in required_vars.items():
        if not value or 'your-' in value or 'your_' in value:
            missing.append(var)
            print(f"  ❌ {var} - Not configured")
        else:
            print(f"  ✅ {var} - Configured")
    
    if missing:
        print(f"\n⚠️  Missing configuration: {', '.join(missing)}")
        print("   Please update your .env file with actual API keys")
        return False
    
    print("✅ All environment variables configured!\n")
    return True

def validate_packages():
    """Validate required Python packages are installed"""
    print("🔍 Validating Python Packages...")
    
    required_packages = [
        ('flask', 'Flask'),
        ('supabase', 'Supabase'),
        ('openai', 'OpenAI'),
        ('dotenv', 'python-dotenv')
    ]
    
    missing = []
    for module, package in required_packages:
        try:
            __import__(module)
            print(f"  ✅ {package} - Installed")
        except ImportError:
            missing.append(package)
            print(f"  ❌ {package} - Missing")
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages installed!\n")
    return True

def validate_supabase_connection():
    """Test Supabase connection"""
    print("🔍 Testing Supabase Connection...")
    
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or 'your-' in url:
            print("  ⚠️  Supabase URL not configured")
            return False
        
        supabase = create_client(url, key)
        
        # Try to query the journal_entries table
        result = supabase.table('journal_entries').select('*').limit(1).execute()
        
        print("  ✅ Supabase connection successful!")
        print(f"  ✅ journal_entries table accessible")
        return True
        
    except Exception as e:
        print(f"  ❌ Supabase connection failed: {str(e)}")
        print("  💡 Make sure you've run database/setup.sql in Supabase SQL Editor")
        return False

def validate_openai_connection():
    """Test OpenAI API connection"""
    print("\n🔍 Testing OpenAI Connection...")
    
    try:
        from openai import OpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key or 'your-' in api_key:
            print("  ⚠️  OpenAI API key not configured")
            return False
        
        client = OpenAI(api_key=api_key)
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Say 'OK' if you can hear me"}],
            max_tokens=5
        )
        
        print("  ✅ OpenAI API connection successful!")
        print(f"  ✅ GPT-4o model accessible")
        return True
        
    except Exception as e:
        print(f"  ❌ OpenAI connection failed: {str(e)}")
        print("  💡 Check your API key and ensure you have GPT-4o access")
        return False

def validate_file_structure():
    """Validate all required files exist"""
    print("\n🔍 Validating File Structure...")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'database/setup.sql',
        'static/js/voice-input.js',
        'static/js/writing-prompts.js',
        'static/css/prompts.css',
        'SETUP.md',
        '.env.example'
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            missing.append(file)
            print(f"  ❌ {file} - Missing")
    
    if missing:
        print(f"\n⚠️  Missing files: {', '.join(missing)}")
        return False
    
    print("✅ All required files present!\n")
    return True

def main():
    """Run all validation checks"""
    print("="*60)
    print("AI Mental Wellness Journal - Validation Script")
    print("Vibe Coding Implementation Checker")
    print("="*60 + "\n")
    
    results = {
        'Packages': validate_packages(),
        'File Structure': validate_file_structure(),
        'Environment': validate_environment(),
    }
    
    # Only test connections if environment is configured
    if results['Environment']:
        results['Supabase'] = validate_supabase_connection()
        results['OpenAI'] = validate_openai_connection()
    else:
        print("⏭️  Skipping connection tests (environment not configured)\n")
    
    # Summary
    print("="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check:20} {status}")
    
    all_passed = all(results.values())
    
    print("="*60)
    if all_passed:
        print("🎉 ALL CHECKS PASSED!")
        print("Your application is ready to run!")
        print("\nNext steps:")
        print("  1. python app.py")
        print("  2. Visit http://localhost:5000")
        print("  3. Sign up and start journaling!")
    else:
        print("⚠️  SOME CHECKS FAILED")
        print("Please fix the issues above before running the application")
        print("\nRefer to SETUP.md for detailed instructions")
    
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
