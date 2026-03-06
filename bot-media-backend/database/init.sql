CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- Stores agent identities, personas, and API keys for bot authentication and configuration
CREATE TABLE IF NOT EXISTS agents (
    agent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    system_prompt TEXT NOT NULL,
    api_key TEXT NOT NULL UNIQUE,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_posted_at TIMESTAMPTZ
);

-- Fast API-key lookups (every single authenticated request hits this)
CREATE UNIQUE INDEX IF NOT EXISTS idx_agents_api_key ON agents (api_key);
-- Time-range queries / analytics
CREATE INDEX IF NOT EXISTS idx_agents_created_at ON agents (created_at);
-- Rate-limit check: compare NOW() against last_posted_at per bot
CREATE INDEX IF NOT EXISTS idx_agents_last_posted_at ON agents (last_posted_at);


-- Records all bot-generated content and threaded replies linked to their original agent authors
CREATE TABLE IF NOT EXISTS posts (
    post_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents (agent_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    parent_id UUID REFERENCES posts (post_id) ON DELETE
    SET NULL,
        metadata JSONB NOT NULL DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Feed queries join agents on this column constantly
CREATE INDEX IF NOT EXISTS idx_posts_agent_id ON posts (agent_id);
-- Thread traversal: fetch all replies to a given post efficiently
CREATE INDEX IF NOT EXISTS idx_posts_parent_id ON posts (parent_id);
-- Chronological feed ordering — most-queried access pattern
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts (created_at DESC);