-- Connect to PostgreSQL and run these commands to set up the database

-- Create a new database for the application
CREATE DATABASE pdf_chat;

-- Connect to the new database
\c pdf_chat

-- Install the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the table for storing embeddings
CREATE TABLE IF NOT EXISTS pdf_embeddings (
    id SERIAL PRIMARY KEY,
    chunk TEXT,
    embedding vector(768)
);

-- Create an index for faster similarity search
-- You can choose between these index types based on your needs:

-- Option 1: HNSW index (faster queries, slower build time)
CREATE INDEX ON pdf_embeddings USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- Option 2: IVFFlat index (good balance between build time and query performance)
-- CREATE INDEX ON pdf_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Grant necessary permissions if you're using a different user
-- GRANT ALL PRIVILEGES ON DATABASE pdf_chat TO your_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;
