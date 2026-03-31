-- TechCorp Customer Success AI Agent - Database Schema
-- Exercise 2.1 - Complete PostgreSQL Schema
-- 8 Tables, 13 Indexes

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLE 1: customers
-- Core customer table storing primary contact information
-- ============================================================================
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- ============================================================================
-- TABLE 2: customer_identifiers
-- Additional identifiers for cross-channel customer recognition
-- ============================================================================
CREATE TABLE customer_identifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    identifier_type VARCHAR(50) NOT NULL,
    identifier_value VARCHAR(255) NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(identifier_type, identifier_value)
);

-- ============================================================================
-- TABLE 3: conversations
-- Tracks customer conversations across all channels
-- ============================================================================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    initial_channel VARCHAR(50) NOT NULL,
    current_channel VARCHAR(50),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'active',
    sentiment_score DECIMAL(3,2),
    sentiment_trend VARCHAR(20) DEFAULT 'stable',
    resolution_type VARCHAR(50),
    escalated_to VARCHAR(255),
    topics_discussed TEXT[],
    metadata JSONB DEFAULT '{}'
);

-- ============================================================================
-- TABLE 4: messages
-- Individual messages within conversations
-- ============================================================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,
    direction VARCHAR(20) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tokens_used INTEGER DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    tool_calls JSONB DEFAULT '[]',
    channel_message_id VARCHAR(255),
    delivery_status VARCHAR(50) DEFAULT 'pending',
    sentiment_score DECIMAL(3,2),
    metadata JSONB DEFAULT '{}'
);

-- ============================================================================
-- TABLE 5: tickets
-- Support tickets linked to conversations
-- ============================================================================
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    customer_id UUID REFERENCES customers(id),
    source_channel VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'open',
    subject TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    escalation_reason TEXT,
    assigned_to VARCHAR(255),
    metadata JSONB DEFAULT '{}'
);

-- ============================================================================
-- TABLE 6: knowledge_base
-- Product documentation and help articles
-- ============================================================================
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    view_count INTEGER DEFAULT 0
);

-- ============================================================================
-- TABLE 7: agent_metrics
-- Performance metrics for the AI agent
-- ============================================================================
CREATE TABLE agent_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    channel VARCHAR(50),
    dimensions JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- TABLE 8: escalations
-- Escalated tickets requiring human intervention
-- ============================================================================
CREATE TABLE escalations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID REFERENCES tickets(id),
    customer_id UUID REFERENCES customers(id),
    reason TEXT NOT NULL,
    urgency VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255),
    notes TEXT
);

-- ============================================================================
-- INDEXES (13 total)
-- ============================================================================

-- Customer indexes
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_phone ON customers(phone);

-- Customer identifiers index
CREATE INDEX idx_customer_identifiers_value 
    ON customer_identifiers(identifier_value);

-- Conversation indexes
CREATE INDEX idx_conversations_customer 
    ON conversations(customer_id);
CREATE INDEX idx_conversations_status 
    ON conversations(status);
CREATE INDEX idx_conversations_channel 
    ON conversations(initial_channel);

-- Message indexes
CREATE INDEX idx_messages_conversation 
    ON messages(conversation_id);
CREATE INDEX idx_messages_channel 
    ON messages(channel);

-- Ticket indexes
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_channel 
    ON tickets(source_channel);
CREATE INDEX idx_tickets_customer 
    ON tickets(customer_id);

-- Escalation index
CREATE INDEX idx_escalations_ticket 
    ON escalations(ticket_id);

-- Metrics index
CREATE INDEX idx_agent_metrics_recorded 
    ON agent_metrics(recorded_at);

-- ============================================================================
-- SCHEMA COMPLETE
-- ============================================================================
