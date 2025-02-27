import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from pypdf import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
import psycopg2
from pgvector.psycopg2 import register_vector
from langchain_core.documents import Document

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
db_url = os.getenv("DATABASE_URL")


def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text


def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks


def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    chunk_embeddings = embeddings.embed_documents(text_chunks)

    # Connect to PostgreSQL
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # Enable vector extension
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create table if it doesn't exist (with correct vector type)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pdf_embeddings (
        id SERIAL PRIMARY KEY,
        chunk TEXT,
        embedding vector(768)
    )
    """)
    # Clear existing data
    cur.execute("TRUNCATE TABLE pdf_embeddings")

    # Insert chunks and embeddings
    for chunk, embedding in zip(text_chunks, chunk_embeddings):
        cur.execute(
            "INSERT INTO pdf_embeddings (chunk, embedding) VALUES (%s, %s::vector)",
            (chunk, embedding)
        )

    conn.commit()
    cur.close()
    conn.close()


def get_conversational_chain():
    prompt_template = """
    Answer the question based on the provided context and conversation history.
    If the answer isn't directly in the context but can be inferred from the conversation history, use that information.
    If you don't have enough information to answer accurately, provide a general response based on your knowledge.
    Avoid saying "I don't have enough information" unless absolutely necessary.
    Avoid saying "Based on the provided text" or similar phrases.

    history: {history}
    Context: {context}
    Question: {question}
    Answer:
    """
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question", "history"]
    )
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain


def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    question_embedding = embeddings.embed_query(user_question)

    # Connect to PostgreSQL
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    register_vector(conn)

    # Query the most similar chunks
    cur.execute(
        "SELECT chunk FROM pdf_embeddings "
        "ORDER BY embedding <-> %s::vector "
        "LIMIT 5",
        (question_embedding,)
    )
    similar_chunks = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    # Use session state to maintain history
    if 'history' not in st.session_state:
        st.session_state.history = []

    # Format history for the model - include the full conversation context
    formatted_history = "\n".join([f"Q: {item['question']}\nA: {item['answer']}" for item in st.session_state.history])

    # Pass to Gemini
    chain = get_conversational_chain()

    # If no relevant chunks are found but we have conversation history,
    # use that as context to maintain conversation continuity
    if not similar_chunks and st.session_state.history:
        # Create a context from the most recent exchanges
        context_from_history = formatted_history
        similar_chunks = [context_from_history]

    # If we still have no context, provide an empty context but allow the model
    # to answer from its general knowledge
    if not similar_chunks:
        similar_chunks = ["No specific context available."]

    response = chain.invoke(
        {
            "input_documents": [Document(page_content=chunk, metadata={}) for chunk in similar_chunks], 
            "question": user_question,
            "history": formatted_history
        },
        return_only_outputs=True
    )
    answer = response["output_text"]

    # Update history in session state
    st.session_state.history.append({"question": user_question, "answer": answer})

    # Clear the input box
    st.session_state.input = ""


def display_chat_history():
    """Display the chat history in a more organized way"""
    if 'history' in st.session_state and st.session_state.history:
        for i, exchange in enumerate(st.session_state.history):
            # User message
            with st.chat_message("user"):
                st.write(exchange['question'])

            # Bot response
            with st.chat_message("assistant"):
                st.write(exchange['answer'])


def main():
    st.set_page_config(page_title="Chat with PDFs using Gemini")
    st.header("Chat with PDFs using Gemini 1.5 Flash")

    # Initialize session state for chat history if it doesn't exist
    if 'history' not in st.session_state:
        st.session_state.history = []

    # Display chat history
    display_chat_history()

    # User input field
    user_question = st.chat_input("Ask a question about your PDFs:")
    if user_question:
        user_input(user_question)
        # Force a rerun to display the new message
        st.rerun()

    with st.sidebar:
        st.title("Upload PDFs")
        pdf_docs = st.file_uploader(
            "Upload your PDF files", accept_multiple_files=True
        )
        if st.button("Process"):
            with st.spinner("Processing..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                # Clear conversation history when uploading new documents
                st.session_state.history = []
                st.success("PDFs processed successfully!")

        # Add a button to clear conversation history
        if st.button("Clear Conversation"):
            st.session_state.history = []
            st.rerun()


if __name__ == "__main__":
    main()
