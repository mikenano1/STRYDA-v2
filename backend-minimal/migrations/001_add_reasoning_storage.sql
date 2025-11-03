-- Migration: Add reasoning trace storage for GPT-5/o1 models
-- Date: 2025-11-02
-- Purpose: Capture full GPT-5 response payloads for deferred parsing

-- Create reasoning_responses table to store GPT-5 traces
CREATE TABLE IF NOT EXISTS reasoning_responses (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    session_id VARCHAR(255),
    query TEXT NOT NULL,
    intent VARCHAR(50),
    model VARCHAR(100),
    reasoning_trace JSONB,  -- Full model_dump() from GPT-5 response
    final_answer TEXT,  -- Extracted answer (may be empty for GPT-5)
    metadata JSONB,  -- Extraction metadata (extraction_path, raw_len, etc.)
    fallback_used BOOLEAN DEFAULT FALSE,
    response_time_ms INTEGER,
    INDEX idx_session_id (session_id),
    INDEX idx_model (model),
    INDEX idx_created_at (created_at)
);

-- Add reasoning fields to existing chat_messages table (if it doesn't have them)
-- This allows linking chat history with reasoning traces
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'chat_messages' AND column_name = 'reasoning_trace'
    ) THEN
        ALTER TABLE chat_messages ADD COLUMN reasoning_trace JSONB;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'chat_messages' AND column_name = 'final_answer'
    ) THEN
        ALTER TABLE chat_messages ADD COLUMN final_answer TEXT;
    END IF;
END $$;

-- Create index for efficient reasoning trace queries
CREATE INDEX IF NOT EXISTS idx_reasoning_responses_model ON reasoning_responses(model);
CREATE INDEX IF NOT EXISTS idx_reasoning_responses_session ON reasoning_responses(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_reasoning ON chat_messages(reasoning_trace) WHERE reasoning_trace IS NOT NULL;

COMMENT ON TABLE reasoning_responses IS 'Stores full GPT-5/o1 reasoning model responses for deferred parsing and analysis';
COMMENT ON COLUMN reasoning_responses.reasoning_trace IS 'Full response.model_dump() JSON including hidden reasoning tokens';
COMMENT ON COLUMN reasoning_responses.final_answer IS 'Extracted final answer text (empty if extraction failed)';
COMMENT ON COLUMN reasoning_responses.metadata IS 'Extraction metadata: extraction_path, raw_len, json_ok, etc.';
