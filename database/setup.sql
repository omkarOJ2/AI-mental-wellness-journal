-- Supabase Database Setup for AI Mental Wellness Journal
-- Run this SQL in your Supabase SQL Editor

-- Create journal_entries table
CREATE TABLE IF NOT EXISTS journal_entries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sentiment_score DECIMAL(3,2) NOT NULL,
    emotions JSONB DEFAULT '[]'::jsonb,
    key_themes JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_journal_entries_user_id ON journal_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_journal_entries_created_at ON journal_entries(created_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view their own entries" ON journal_entries;
DROP POLICY IF EXISTS "Users can insert their own entries" ON journal_entries;
DROP POLICY IF EXISTS "Users can update their own entries" ON journal_entries;
DROP POLICY IF EXISTS "Users can delete their own entries" ON journal_entries;

-- RLS Policies: Users can only access their own journal entries
CREATE POLICY "Users can view their own entries"
    ON journal_entries
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own entries"
    ON journal_entries
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own entries"
    ON journal_entries
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own entries"
    ON journal_entries
    FOR DELETE
    USING (auth.uid() = user_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_journal_entries_updated_at ON journal_entries;
CREATE TRIGGER update_journal_entries_updated_at
    BEFORE UPDATE ON journal_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Optional: Create a view for weekly statistics (users can only see their own stats)
CREATE OR REPLACE VIEW weekly_sentiment_stats AS
SELECT 
    user_id,
    DATE_TRUNC('week', created_at) as week_start,
    AVG(sentiment_score) as avg_sentiment,
    COUNT(*) as entry_count,
    jsonb_agg(DISTINCT emotions) as all_emotions
FROM journal_entries
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY user_id, DATE_TRUNC('week', created_at);

-- Enable RLS on the view
ALTER VIEW weekly_sentiment_stats SET (security_barrier = true);

-- Grant access to authenticated users
GRANT SELECT ON weekly_sentiment_stats TO authenticated;

-- Verification queries (optional - run these to verify setup)
-- SELECT * FROM journal_entries LIMIT 1;
-- SELECT * FROM weekly_sentiment_stats LIMIT 1;
