-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create necessary tables for the application
CREATE TABLE IF NOT EXISTS pdf_embeddings (
    id SERIAL PRIMARY KEY,
    chunk TEXT,
    embedding vector(768)
);

-- Create an optimized index for similarity search
CREATE INDEX IF NOT EXISTS pdf_embeddings_embedding_idx ON pdf_embeddings
USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
