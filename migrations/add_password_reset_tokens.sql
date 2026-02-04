-- ============================================
-- Password Reset System Migration
-- Description: Creates password_reset_tokens table for email-based password recovery
-- Date: 2026-02-04
-- ============================================

-- Create password_reset_tokens table
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP WITH TIME ZONE NULL,

-- Foreign key constraint
CONSTRAINT fk_password_reset_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_reset_token_hash ON password_reset_tokens (token_hash);

CREATE INDEX IF NOT EXISTS idx_reset_user_id ON password_reset_tokens (user_id);

CREATE INDEX IF NOT EXISTS idx_reset_expires_at ON password_reset_tokens (expires_at);

CREATE INDEX IF NOT EXISTS idx_reset_is_used ON password_reset_tokens (is_used);

CREATE INDEX IF NOT EXISTS idx_reset_user_expires ON password_reset_tokens (user_id, expires_at);

-- Add comment to table
COMMENT ON
TABLE password_reset_tokens IS 'Stores password reset tokens for email-based password recovery';

COMMENT ON COLUMN password_reset_tokens.token_hash IS 'SHA-256 hash of the reset token';

COMMENT ON COLUMN password_reset_tokens.expires_at IS 'Token expiration timestamp (30 minutes from creation)';

COMMENT ON COLUMN password_reset_tokens.is_used IS 'Flag to prevent token reuse';

COMMENT ON COLUMN password_reset_tokens.used_at IS 'Timestamp when token was used';

-- Verify table creation
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE
    table_name = 'password_reset_tokens'
ORDER BY ordinal_position;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Password reset tokens table created successfully';
END $$;