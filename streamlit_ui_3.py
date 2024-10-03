import os
import streamlit as st
import openai
from dotenv import load_dotenv
import fitz  # PyMuPDF
import logging
import time
from docx import Document
import pandas as pd
from transformers import AutoTokenizer, TFAutoModel
import tensorflow as tf

# Load environment variables
load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")
assistant_id = os.environ.get("ASSISTANT_ID")

# Initialize OpenAI client
client = openai.OpenAI()

# Configure logging
logging.basicConfig(level=logging.INFO)

def extract_text_from_word(file_path):
    text = ""
    try:
        doc = Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        logging.error(f"Error extracting text from Word file: {e}")
        raise
    return text

# Function for Text Embedding with TensorFlow
def embed_text_large(text):
    try:
        # Load the tokenizer and model for XLM-RoBERTa Large
        model_name = "xlm-roberta-large"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = TFAutoModel.from_pretrained(model_name)
        
        # Tokenize the input text
        inputs = tokenizer(text, return_tensors="tf", padding=True, truncation=True)
        
        # Get the embeddings from the model (CLS token represents the whole sentence)
        outputs = model(**inputs)
        embedding = outputs.last_hidden_state[:, 0, :]  # CLS token
        
        return embedding.numpy().tolist()
    except Exception as e:
        logging.error(f"Error embedding text: {e}")
        raise

def contract_check(contract_text, regulations):
    """
    Check the contract against specified regulations.

    Parameters:
    contract_text (str): The text of the contract to be checked.
    regulations (list): A list of regulations to check against.

    Returns:
    dict: The response from the assistant.
    """
    # Generate embeddings for the contract text
    embeddings = embed_text_large(contract_text)
    logging.info("Embeddings generated for the contract text.")

    response = client.beta.assistants.runs.create(
        assistant_id=assistant_id,
        thread_id=thread.id,
        function_call={"name": "contract_check", "arguments": {"contract_text": contract_text, "embeddings": embeddings}}
    )
   
    return response

def main():
    st.title("Contract Checking Assistant")

    # Validate API key and assistant ID
    if not openai.api_key or not assistant_id:
        st.error("Please ensure that OPENAI_API_KEY and ASSISTANT_ID are set in your environment variables.")
        return

    # Upload contract file
    uploaded_file = st.file_uploader("Upload Contract File")
    user_message = st.text_input("Enter your message with the contract:")

    if uploaded_file is not None and user_message:
        try:
            contract_text = extract_text_from_word(uploaded_file)
            st.write(f"Length of contract text: {len(contract_text)}")
        except Exception as e:
            st.error(f"Error reading the file: {e}")
            return

        # Generate embeddings for the contract text
        embeddings = embed_text_large(contract_text)
        st.write("Embeddings generated for the contract text.")

        # Check usage limit
        usage_limit = check_usage_limit()
        if usage_limit == 0:
            st.error("Usage limit reached. Please try again later.")
            return

        # Create a thread
        st.write("Creating a thread...")
        try:
            thread = client.beta.threads.create()
            st.write(f"Thread created with ID: {thread.id}")
        except Exception as e:
            st.error(f"Error creating thread: {e}")
            return

        # Send the contract text and user message to the thread
        st.write("Sending contract text and user message to the thread...")
        try:
            message = client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"{user_message}\n\n{contract_text}"
            )
            st.write("Message sent to the thread.")
        except Exception as e:
            st.error(f"Error sending message to thread: {e}")
            return
        

        #generate a response from assistance 
        run = client.beta.threads.runs.create(
            assistant_id = assistant_id,
            thread_id= thread.id
        )
        run = client.beta.threads.runs.retrieve(
        thread_id = thread.id,
        run_id = run.id)

        print(run.status)



        # Wait for the response
        while response.status != "completed":
            time.sleep(1)
            try:
                response = client.beta.assistants.retrieve(
                    assistant_id = assistant_id,
                    run_id = run.id                   
                )
            except Exception as e:
                st.error(f"Error retrieving response: {e}")
                return

        # Display the assistant's response
        st.text_area("Assistant Response", value=response.outputs[0].text)

def check_usage_limit():
    # Placeholder function to check usage limit
    # Replace with actual implementation to check usage limit from OpenAI API
    return 1  # Assume usage limit is not zero for this example

if __name__ == "__main__":
    main()