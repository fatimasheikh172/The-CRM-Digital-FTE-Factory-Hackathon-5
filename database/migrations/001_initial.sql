-- Migration 001: Initial Schema
-- Created: 2026-03-14
-- Description: Initial database schema with 8 tables and 13 indexes

-- This migration creates the complete schema for the TechCorp Customer Success AI Agent

-- Run the complete schema
\i database/schema.sql

-- Record migration
INSERT INTO schema_migrations (version, applied_at) 
VALUES ('001', NOW())
ON CONFLICT (version) DO NOTHING;
