# Chat with PDFs using Gemini and PostgreSQL Vector Database

This application allows users to chat with PDF documents using Google's Gemini 1.5 Flash model and vector embeddings stored in a PostgreSQL database with pgvector extension.

## Overview

This project enables interactive conversations with PDF documents by leveraging:
- Text extraction from PDF files
- Vector embeddings creation using Google's embedding model
- Storage and retrieval of vectors using PostgreSQL with pgvector extension
- Conversational AI powered by Google's Gemini 1.5 Flash model
- Streamlit for a user-friendly chat interface

## Features

- Upload multiple PDF documents
- Interactive chat with PDF content
- Conversation memory that retains context
- Real-time similarity search using vector embeddings
- Clean and intuitive interface

## Prerequisites

- Python 3.8+
- PostgreSQL database with pgvector extension installed
- Google AI API key
- Required Python packages (see requirements.txt)

## Setup Instructions

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd chatWithPDFsWithVectorDB

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .example.env .env
# Edit .env with your actual credentials
```

### 2. PostgreSQL and pgvector Setup

#### Installing PostgreSQL

If you haven't installed PostgreSQL yet:

- **macOS**: `brew install postgresql`
- **Ubuntu/Debian**: `sudo apt install postgresql postgresql-contrib`
- **Windows**: Download installer from [postgresql.org](https://www.postgresql.org/download/windows/)

#### Setting up pgvector

1. Connect to PostgreSQL:
   ```bash
   psql -U postgres
   ```

2. Create a database for the application:
   ```sql
   CREATE DATABASE pdf_chat;
   \c pdf_chat
   ```

3. Install the pgvector extension:
   ```sql
   CREATE EXTENSION vector;
   ```

4. Create the table for storing embeddings (this will be created automatically by the application, but you can create it manually if needed):
   ```sql
   CREATE TABLE pdf_embeddings (
       id SERIAL PRIMARY KEY,
       chunk TEXT,
       embedding vector(768)
   );
   ```

5. Optionally, create an index for faster similarity search:
   ```sql
   CREATE INDEX ON pdf_embeddings USING hnsw (embedding vector_cosine_ops);
   ```

### 3. Running the Application

```bash
streamlit run main.py
```

The application will be available at http://localhost:8501 by default.

## How It Works

### 1. PDF Processing Pipeline

1. **Text Extraction**: Raw text is extracted from uploaded PDF files
2. **Text Chunking**: The text is split into manageable chunks with some overlap
3. **Embedding Generation**: Each chunk is converted to a vector embedding (768-dimensional vector)
4. **Storage**: Chunks and their embeddings are stored in PostgreSQL

### 2. Query Processing Pipeline

1. **Question Embedding**: User question is converted to a vector embedding
2. **Similarity Search**: PostgreSQL with pgvector finds the most similar chunks using vector similarity
3. **Context Assembly**: Top similar chunks are retrieved and used as context
4. **Response Generation**: Gemini 1.5 generates an answer based on the context and conversation history

## Understanding Vector Database with PostgreSQL and pgvector

### What is pgvector?

pgvector is an extension for PostgreSQL that adds support for vector similarity search. It enables PostgreSQL to store and query vector embeddings efficiently.

### Key Components:

- **Vector Type**: pgvector adds a new `vector` data type to PostgreSQL
- **Similarity Operators**: Provides operators for calculating distances between vectors
- **Indexing Methods**: Supports multiple indexing methods for efficient similarity search:
  - `ivfflat`: Inverted file with flat quantization (fast but approximate)
  - `hnsw`: Hierarchical Navigable Small World graphs (faster queries but slower index creation)

### Advantages of Using PostgreSQL as a Vector Database

1. **Integration with Existing Data**: Store vectors alongside other relational data
2. **SQL Interface**: Use familiar SQL syntax for complex queries
3. **ACID Compliance**: Benefit from PostgreSQL's strong transactional guarantees
4. **Cost-Effective**: Avoid additional costs of specialized vector database services
5. **Scalability**: Leverage PostgreSQL's mature scaling capabilities

### How We Use pgvector in This Project

In our implementation:

1. We embed PDF chunks into 768-dimensional vectors (Google's embedding model)
2. We store these vectors in a PostgreSQL table using the vector data type
3. For each query, we:
   - Convert the question to an embedding vector
   - Use the `<->` operator (cosine distance) to find similar chunks
   - Retrieve the top 5 most relevant chunks for context

Example query used in our code:
```sql
SELECT chunk FROM pdf_embeddings
ORDER BY embedding <-> %s::vector
LIMIT 5
```

## Usage Guide

1. **Upload PDFs**:
   - Use the sidebar to upload one or more PDF files
   - Click "Process" to extract and embed the content

2. **Ask Questions**:
   - Type your question in the chat input field
   - View the AI's response based on the PDF content
   - Continue the conversation naturally, referring to previous exchanges

3. **Clear Conversation**:
   - Use the "Clear Conversation" button in the sidebar to start over

## Project Structure

```
chatWithPDFsWithVectorDB/
├── .env                  # Environment variables (API keys, DB connection)
├── .example.env          # Example environment variables template
├── .gitignore            # Files to be ignored by Git
├── main.py               # Main application code with Streamlit interface
├── README.md             # Project documentation
└── requirements.txt      # Python dependencies
```

## Further Improvements

- Implement user authentication and document access control
- Add support for more file formats beyond PDFs
- Optimize vector storage with custom indexes
- Improve chunking strategies for better context retrieval
- Add metadata filtering for more targeted searches

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

Feel free to contribute to this project by submitting issues or pull requests.
