%%writefile app.py
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables import RunnablePassthrough
from langchain.chains import create_retrieval_chain
import fal_client
import requests
import os
import tempfile



# Initialize LLM with API Keys directly
def initialize_llm(openrouter_api_key):
    return ChatOpenAI(
        model="deepseek/deepseek-chat",
        openai_api_key=openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1"
    )


# Function to load and process documents
def load_and_process_docs(uploaded_file, website_url):
    all_docs = []

    if uploaded_file:
         try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(uploaded_file.read())
                temp_file_path = temp_file.name
            loader = PyPDFLoader(temp_file_path)
            docs = loader.load()
            all_docs.extend(docs)
            os.remove(temp_file_path)
         except Exception as e:
            st.error(f"Error processing PDF: {e}")
            return None

    if website_url:
        try:
            loader = WebBaseLoader(website_url)
            docs = loader.load()
            all_docs.extend(docs)
        except Exception as e:
            st.error(f"Error fetching website: {e}")
            return None

    if not all_docs:
        return None

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = text_splitter.split_documents(all_docs)
    return split_docs



# Function to generate podcast conversation
def generate_podcast(topic, context_docs, llm):
    podcast_template = ChatPromptTemplate.from_template("""
        Create an engaging conversation between two speakers discussing the topic: {topic}

        Context:
        {context}

        Requirements:
        - Generate exactly 5 back-and-forth exchanges
        - Make it natural and conversational
        - Include specific details about the {topic}
        - Each line should start with either "Speaker 1:" or "Speaker 2:"
        - The response of each speaker should be at most 20 words. The conversation has to be insightful and engaging.
        - You are allowed to write only in the below format. Just give the output in the below format in a single string. No additional delimiters.

        Example of Format (Create new content about {topic} and {context}):
        Speaker 1: Hey, did you catch the game last night?
        Speaker 2: Of course! What a match—it had me on the edge of my seat.
        Speaker 1: Same here! That last-minute goal was unreal. Who's your MVP?
        Speaker 2: Gotta be the goalie. Those saves were unbelievable.

    """)


    if context_docs:
        retriever = create_retrieval_chain(
            {
                "context": lambda x: x["docs"],
                "topic": lambda x: x["topic"],
            },
            (RunnablePassthrough.assign(docs=lambda x: x["docs"]) | create_stuff_documents_chain(llm,podcast_template)),
        )

        response = retriever.invoke({"docs": context_docs,"topic": topic})
        conversation = response
    else:
        chain = podcast_template | llm | StrOutputParser()
        conversation = chain.invoke({"topic": topic, "context": ""})
    return conversation



# Function to generate audio
def generate_audio(conversation, fal_api_key):
    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                st.write(log["message"])

    result = fal_client.subscribe(
        "fal-ai/playht/tts/ldm",
        {
            "input": conversation,
            "voices": [
                {
                    "voice": "Jennifer (English (US)/American)",
                    "turn_prefix": "Speaker 1: "
                },
                {
                    "voice": "Dexter (English (US)/American)",
                    "turn_prefix": "Speaker 2: "
                }
            ]
        },
         api_key=fal_api_key,
        with_logs=True,
        on_queue_update=on_queue_update,
    )
    return result.get("audio", {}).get("url")



# Streamlit App
st.title("Podcast Generator")
st.write("❤️ Built by [Build Fast with AI](https://buildfastwithai.com/genai-course)")


# Sidebar for API Keys and Inputs
with st.sidebar:
    st.header("API Keys")
    openrouter_api_key = st.text_input("OpenRouter API Key", type="password")
    fal_api_key = st.text_input("FAL API Key", type="password")
    st.header("Podcast Inputs")
    topic = st.text_input("Enter a topic for the podcast:")
    uploaded_file = st.file_uploader("Upload a PDF Document", type=["pdf"])
    website_url = st.text_input("Enter a Website URL")



if st.button("Generate Podcast"):
    with st.spinner("Generating..."):
        if not openrouter_api_key or not fal_api_key:
            st.error("Please enter both API Keys in the sidebar.")
        else:
            llm = initialize_llm(openrouter_api_key)
            context_docs = load_and_process_docs(uploaded_file, website_url)
            if topic:
                conversation = generate_podcast(topic, context_docs, llm)
                if conversation:
                    st.subheader("Generated Conversation:")
                    st.write(conversation)
                    audio_url = generate_audio(conversation, fal_api_key)
                    if audio_url:
                        st.subheader("Listen to the Podcast:")
                        st.audio(audio_url)
                    else:
                        st.error("Failed to generate audio.")
                else:
                    st.error("Failed to generate conversation.")
            else:
                  st.error("Please enter a topic.")
