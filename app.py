import streamlit as st
import os
import tempfile
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import fal_client
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import CharacterTextSplitter
from pypdf import PdfReader  # Using pypdf
from docx import Document #Required import for docx with correct library

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


# --- Function for Generating Podcast Transcript ---
def generate_podcast_transcript(topic, text=None, openai_api_key=None):
    if text:
        podcast_template = ChatPromptTemplate.from_template("""
        Create an engaging conversation between two speakers discussing the topic of the below text: 
        {text}
        Requirements:
            - Generate exactly 5 back-and-forth exchanges
            - Make it natural and conversational
            - Include specific details about the topic in the text
            - Each line should start with either "Speaker 1:" or "Speaker 2:"
            - The response of the each speaker should be at most 20 words.
            - The conversation has to be insightful, engaging, explanatory, deep diving and educational.

        It should be in the style of a podcast where one speaker slightly is more knowledgeable than the other.
        You are allowed to write only in the below format. Just give the output in the below format in a single string. No additional delimiters.
        The content should be explanatory, deep diving and educational.

            Speaker 1: Hey, did you catch the game last night?
            Speaker 2: Of course! What a match—it had me on the edge of my seat.
            Speaker 1: Same here! That last-minute goal was unreal. Who's your MVP?
            Speaker 2: Gotta be the goalie. Those saves were unbelievable.


        Remember: Create completely new dialogue about the text, don't use the above example.
        """)
        llm = ChatOpenAI(
        model="deepseek/deepseek-chat",
        openai_api_key=openai_api_key,
        openai_api_base="https://openrouter.ai/api/v1"
        )
    else:
        podcast_template = ChatPromptTemplate.from_template("""
        Create an engaging conversation between two speakers discussing the topic: {topic}

        Requirements:
        - Generate exactly 5 back-and-forth exchanges
        - Make it natural and conversational
        - Include specific details about the {topic}
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
            openai_api_key=openai_api_key,
            openai_api_base="https://openrouter.ai/api/v1"
        )
    if text:
       chain = podcast_template | llm
       response = chain.invoke({"text": text})
    else:
       chain = podcast_template | llm
       response = chain.invoke({"topic": topic})
    return response.content


# --- Function for Generating Podcast with Audio ---
def generate_podcast(topic, text=None, openai_api_key=None, fal_key=None):
    if text:
        st.write(f"\n🎙️ Generating podcast transcript about text provided:")
        st.write("-" * 50)
    else:
        st.write(f"\n🎙️ Generating podcast transcript about: {topic}")
        st.write("-" * 50)

    # Get transcript first
    try:
        with st.spinner("Generating Transcript..."):
            transcript_result = generate_podcast_transcript(topic, text, openai_api_key)
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
        if isinstance(fal_client.InProgress):
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
                api_key = fal_key,
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
    st.title("🎙️ Podcast Generator")
    st.write("❤️ Built by [Build Fast with AI](https://buildfastwithai.com/genai-course)")

    # API Key Input
    openai_api_key = st.sidebar.text_input("Enter your OpenRouter API Key:", type="password")
    fal_key = st.sidebar.text_input("Enter your FAL API Key:", type="password")

    # --- Sidebar for Navigation ---
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Topic-Based Podcast", "URL-Based Podcast","Document-Based Podcast"])
    
    if page == "Topic-Based Podcast":
        st.header("Generate Podcast from Topic")
        topic = st.text_input("Enter podcast topic:")

        if st.button("Generate Podcast"):
            if topic:
                if not openai_api_key:
                     st.warning("Please enter your OpenRouter API key in the sidebar.")
                     return
                if not fal_key:
                    st.warning("Please enter your FAL API key in the sidebar.")
                    return
                podcast_data = generate_podcast(topic, openai_api_key=openai_api_key, fal_key=fal_key)

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
                if not openai_api_key:
                     st.warning("Please enter your OpenRouter API key in the sidebar.")
                     return
                if not fal_key:
                    st.warning("Please enter your FAL API key in the sidebar.")
                    return

                loader = WebBaseLoader(url)
                data = loader.load()
                text = data[0].page_content
                with st.spinner('Scraping URL Content...'):
                    podcast_data = generate_podcast(podcast_title, text, openai_api_key=openai_api_key, fal_key = fal_key)
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
                if not openai_api_key:
                    st.warning("Please enter your OpenRouter API key in the sidebar.")
                    return
                if not fal_key:
                    st.warning("Please enter your FAL API key in the sidebar.")
                    return
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
                    
                    #Split text into chunks using text splitter
                    text_splitter = CharacterTextSplitter(separator="\n",chunk_size = 1000, chunk_overlap = 200, length_function = len)
                    chunks = text_splitter.split_text(text)
                    
                    # Process all the text chunks
                    podcast_text = " ".join(chunks)
                    podcast_data = generate_podcast(podcast_title, podcast_text, openai_api_key=openai_api_key, fal_key = fal_key)
                    
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
