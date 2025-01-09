# Podcast Generator

This Streamlit application allows you to generate podcasts from various sources: a topic, a URL, or a document (txt, pdf, or docx). It leverages Langchain, OpenAI's DeepSeek, Google Gemini, and fal-client for text processing, transcript generation, and audio conversion.

## Features

-   **Topic-Based Podcasts:** Generate a podcast transcript and audio based on a user-provided topic.
-   **URL-Based Podcasts:** Scrape content from a URL, and generate a podcast based on the scraped content.
-   **Document-Based Podcasts:** Upload a document (txt, pdf, or docx) and generate a podcast based on the document's content.
-   **Conversational Style:** The generated podcasts use a conversational format between two speakers, making them engaging and informative.
-   **RAG (Retrieval-Augmented Generation):** Uses RAG for more context-aware podcast generation.
-   **Audio Output:** Provides a playable audio output in the app.


## Setup


1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Set up environment variables:**
    -   Create a `.env` file in the root directory.
    -   Add the following environment variables:
        ```
        FAL_KEY="your_fal_key"
        OPENROUTER_API_KEY="your_openrouter_api_key"
        GOOGLE_API_KEY="your_google_api_key"
        ```
        Replace `"your_fal_key"`, `"your_openrouter_api_key"`, and `"your_google_api_key"` with your actual API keys.
        -   You can find your fal-client API key on the Fal.ai dashboard.
        -   For `OPENROUTER_API_KEY`, you need to register to openrouter.ai and generate one API key.
        -   You will need a Google Cloud Project to generate the Gemini API Key.

3.  **Run the Streamlit application:**
    ```bash
    streamlit run app.py
    ```
    This will launch the app in your default web browser.

## Usage

1.  **Navigate to Different Sections**: Use the sidebar to navigate between "Topic-Based Podcast", "URL-Based Podcast", and "Document-Based Podcast".
2.  **Topic-Based Podcast:**
    -   Enter a topic in the text input field.
    -   Click the "Generate Podcast" button.
    -   The app will display the generated transcript and audio output.
3.  **URL-Based Podcast:**
    -   Enter a URL to scrape content from.
    -   Enter a title for the podcast.
    -   Click the "Generate Podcast from URL" button.
    -   The app will display the generated transcript and audio output.
4.  **Document-Based Podcast:**
    -   Upload a document (txt, pdf, or docx) using the file uploader.
    -   Enter a title for the podcast.
    -   Click the "Generate Podcast from Document" button.
    -   The app will display the generated transcript and audio output.
5.  **Audio Output:**  The app provides a playable audio output embedded in the Streamlit App.

