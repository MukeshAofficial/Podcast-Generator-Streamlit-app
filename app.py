import streamlit as st
import os
import tempfile
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import fal_client
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from pypdf import PdfReader  
from docx import Document 
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate



load_dotenv()  # Load environment variables from .env file


def extract_text_from_pdf(file_path):
    """Extract text from a PDF file using pypdf."""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


def extract_text_from_docx(file_path):
    """Extract text from a DOCX file."""
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
      text += paragraph.text + '\n'
    return text


def extract_text(file_path, file_type):
    """Extract text based on file type."""
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif file_type == "docx":
        return extract_text_from_docx(file_path)
    else:
        return "Unsupported file type."


# --- Function for Generating Podcast Transcript with RAG---
def generate_podcast_transcript_with_rag(topic, text=None):
     
    if text:

        # Split the document into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
        docs = text_splitter.split_text(text)

        # Create a vector store
        vectorstore = Chroma.from_texts(
            texts=docs, embedding=GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        )

        # Create a retriever
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})

        # Initialize Gemini model (ensure API key is set)
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0, max_tokens=None, timeout=None)

        # Define prompt template
        system_prompt = (
            """
Create an engaging conversation between two speakers discussing the topic: {topic}, based on the provided context.

Requirements:
- Generate exactly 5 back-and-forth exchanges
- Make it natural and conversational
- Include specific details about the {topic} based on the provided context.
- Each line should start with either "Speaker 1:" or "Speaker 2:"

Here's an example of the format (but create NEW content about {topic} based on the given context, don't copy this example):
Speaker 1: [First speaker's line]
Speaker 2: [Second speaker's line]

The response of the each speaker should be at most 20 words. The conversation has to be insightful, engaging, explanatory, deep diving and educational.

It should be in the style of a podcast where one speaker slightly is more knowledgeable than the other.

You are allowed to write only in the below format. Just give the output in the below format in a single string. No additional delimiters.

The content should be explanatory, deep diving and educational.

Speaker 1: Hey, did you catch the game last night?
Speaker 2: Of course! What a match—it had me on the edge of my seat.
Speaker 1: Same here! That last-minute goal was unreal. Who's your MVP?
Speaker 2: Gotta be the goalie. Those saves were unbelievable.

Remember: Create completely new dialogue about {topic} based on the given context, don't use the above example.

\n\n
{context}
"""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )

       # Create and run RAG chain
        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        response = rag_chain.invoke({"input": topic, "topic": topic})
        
        # Initialize Deepseek model
        deepseek_llm = ChatOpenAI(
            model="deepseek/deepseek-chat",
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1"
        )

         # Create a prompt for deepseek
        deepseek_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
               
            ]
        )
        
        deepseek_chain =  deepseek_prompt | deepseek_llm

        deepseek_response = deepseek_chain.invoke({"topic": topic, "context": response["answer"]})
        return deepseek_response.content
    else:
        podcast_template = ChatPromptTemplate.from_template("""
Create an engaging conversation between two speakers discussing the topic: {topic}.

Requirements:
- Generate exactly 5 back-and-forth exchanges
- Make it natural and conversational
- Include specific details about the {topic}.
- Each line should start with either "Speaker 1:" or "Speaker 2:"

Here's an example of the format (but create NEW content about {topic}, don't copy this example):
Speaker 1: [First speaker's line]
Speaker 2: [Second speaker's line]

The response of the each speaker should be at most 20 words. The conversation has to be insightful, engaging, explanatory, deep diving and educational.

It should be in the style of a podcast where one speaker slightly is more knowledgeable than the other.

You are allowed to write only in the below format. Just give the output in the below format in a single string. No additional delimiters.

The content should be explanatory, deep diving and educational.

Speaker 1: Hey, did you catch the game last night?
Speaker 2: Of course! What a match—it had me on the edge of my seat.
Speaker 1: Same here! That last-minute goal was unreal. Who's your MVP?
Speaker 2: Gotta be the goalie. Those saves were unbelievable.

Remember: Create completely new dialogue about {topic}, don't use the above example.
""")

        llm = ChatOpenAI(
            model="deepseek/deepseek-chat",
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1"
        )
    
    
       
    chain = podcast_template | llm
    response = chain.invoke({"topic": topic})
    return response.content



# --- Function for Generating Podcast with Audio ---
def generate_podcast(topic, text=None):
    if text:
        st.write(f"\n🎙️ Generating podcast transcript about text provided:")
        st.write("-" * 50)
    else:
        st.write(f"\n🎙️ Generating podcast transcript about: {topic}")
        st.write("-" * 50)

    # Get transcript first
    try:
        with st.spinner("Generating Transcript..."):
            transcript_result = generate_podcast_transcript_with_rag(topic, text)
    except Exception as e:
        st.error(f"Error generating transcript: {e}")
        return None

    st.write("\n✍️ Generated transcript:")
    st.write("-" * 50)
    st.write(transcript_result)

    st.write("\n🔊 Converting transcript to audio...")
    st.write("-" * 50)

    # Progress callback for fal-client
    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                st.write(f"🎵 {log['message']}")

    # Generate audio using fal-client
    try:
        with st.spinner("Generating Audio..."):
            result = fal_client.subscribe(
                "fal-ai/playht/tts/ldm",
                {
                    "input": transcript_result,
                    "voices": [
                        {
                            "voice": "Jennifer (English (US)/American)",
                            "turn_prefix": "Speaker 1: ",
                        },
                        {
                            "voice": "Dexter (English (US)/American)",
                            "turn_prefix": "Speaker 2: ",
                        },
                    ],
                },
                with_logs=True,
                on_queue_update=on_queue_update,
            )

        st.write("\n✅ Audio generation complete!")
        st.write(f"🔗 Audio URL: {result['audio']['url']}")
        return {
            "conversation": transcript_result,
            "audio_url": result["audio"]["url"],
        }

    except Exception as e:
        st.error(f"\n❌ Error generating audio: {str(e)}")
        return {
            "conversation": transcript_result,
            "audio_url": None,
            "error": str(e),
        }


# --- Streamlit App ---
def main():
    st.title("Podcast Generator")

    # Get API Keys from environment variables
    fal_key = os.getenv("FAL_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")


    if not fal_key or not openrouter_key or not google_api_key:
        st.error(
            "Please set FAL_KEY, OPENROUTER_API_KEY and GOOGLE_API_KEY as environment variables or in .env file."
        )
        return

    os.environ["FAL_KEY"] = fal_key
    os.environ["OPENROUTER_API_KEY"] = openrouter_key
    os.environ["GOOGLE_API_KEY"] = google_api_key

    # --- Sidebar for Navigation ---
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Topic-Based Podcast", "URL-Based Podcast","Document-Based Podcast"])
    
    if page == "Topic-Based Podcast":
        st.header("Generate Podcast from Topic")
        topic = st.text_input("Enter podcast topic:")

        if st.button("Generate Podcast"):
            if topic:
                podcast_data = generate_podcast(topic)

                if podcast_data and podcast_data["audio_url"]:
                   st.audio(podcast_data["audio_url"], format="audio/mpeg")
            else:
                st.warning("Please enter a topic!")


    elif page == "URL-Based Podcast":
         st.header("Generate Podcast from URL")
         url = st.text_input("Enter URL to scrape content from:")
         podcast_title = st.text_input("Enter podcast title:")
         if st.button("Generate Podcast from URL"):
            if url and podcast_title:
              try:
                loader = WebBaseLoader(url)
                data = loader.load()
                text = data[0].page_content
                with st.spinner('Scraping URL Content...'):
                    podcast_data = generate_podcast(podcast_title, text)
                if podcast_data and podcast_data["audio_url"]:
                   st.audio(podcast_data["audio_url"], format="audio/mpeg")

              except Exception as e:
                st.error(f"Error scraping URL or generating podcast: {str(e)}")

            else:
              st.warning("Please enter a valid URL and a podcast title")
    elif page == "Document-Based Podcast":
          st.header("Generate Podcast from Document")
          uploaded_file = st.file_uploader("Upload a document (txt, pdf, docx)", type=["txt", "pdf", "docx"])
          podcast_title = st.text_input("Enter podcast title:")
          if st.button("Generate Podcast from Document"):
            if uploaded_file and podcast_title:
              try:
                with st.spinner('Loading and processing document...'):
                  # Create a temporary file
                    temp_file_path = "temp_uploaded_file"
                    with open(temp_file_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    

                    # Determine file type and load accordingly
                    file_extension = uploaded_file.name.split('.')[-1].lower()
                    
                    text = extract_text(temp_file_path, file_extension)
                    if text == "Unsupported file type":
                        st.error(f"Unsupported file type {file_extension}")
                        return
                    
                    # Process the document with RAG for podcast
                    podcast_data = generate_podcast(podcast_title, text)


                    # Delete the temporary file
                    os.remove(temp_file_path)


                    if podcast_data and podcast_data["audio_url"]:
                      st.audio(podcast_data["audio_url"], format="audio/mpeg")


              except Exception as e:
                  st.error(f"Error loading document or generating podcast: {str(e)}")
              
            else:


              st.warning("Please upload a document and enter a podcast title.")
                

if __name__ == "__main__":
    main()