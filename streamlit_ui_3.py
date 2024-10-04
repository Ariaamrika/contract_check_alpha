import os
import streamlit as st
import openai
from dotenv import load_dotenv
import logging
import time
from docx import Document
import pandas as pd
from transformers import AutoTokenizer, TFAutoModel
import tensorflow as tf

# Load environment variables
openai.api_key = st.secrets["OPENAI_API_KEY"]
assistant_id = st.secrets["ASSISTANT_ID"]

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

def contract_check(contract_text, regulations):
    """
    Check the contract against specified regulations.

    Parameters:
    contract_text (str): The text of the contract to be checked.
    regulations (list): A list of regulations to check against.

    Returns:
    dict: The response from the assistant.
    """

    response = client.beta.assistants.runs.create(
        assistant_id=assistant_id,
        thread_id=thread.id,
        function_call={"name": "contract_check", "arguments": {"contract_text": contract_text}}
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
        
        st.write("Wait for the assistant to prossess the contract!")
        

        # Wait for the run to complete
        run = client.beta.threads.runs.create(
        assistant_id=assistant_id,
        thread_id=thread.id)
        print(run.status)


        while run.status not in ["completed", "failed", "requires_action"]:
            run = client.beta.threads.runs.retrieve(
            thread_id = thread.id,
            run_id = run.id        )

        print(run.status)
        time.sleep(5)
        print(run.status)
        

# Check if the run was successful
        if run.status == "completed":
           messages = client.beta.threads.messages.list(
            thread_id = thread.id,)
           
           assistant_response = ''           

           for each in messages:
                assistant_response = assistant_response +each.role + ":" + each.content[0].text.value
                print(each.role + ":" + each.content[0].text.value)
           st.write("Run completed!")
           st.text_area("Assistant Response", assistant_response)

        elif run.status == "failed":
            st.error("The assistant run failed.")
        elif run.status == "requires_action" :
            tools_to_call = run.required_action.submit_tool_outputs.tool_calls
            tools_output_array = []
            for each_tool in tools_to_call:
                tool_call_id = each_tool.id
                function_name = each_tool.function.name
                function_arg = each_tool.function.arguments


                # Initialize output as a string
                output = "False"  # Default as string "False"
                
                if function_name == 'contract_check':
                    output = "True"  # Change to string "True" when contract_check is called

                # Append the output with the correct type (string)
                tools_output_array.append({"tool_call_id": tool_call_id, "output": output})
                # Submitting the tool outputs with the correct types
                run = client.beta.threads.runs.submit_tool_outputs( thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tools_output_array)


                while run.status not in ["completed", "failed", "requires_action"]:
                    run = client.beta.threads.runs.retrieve(
                        thread_id = thread.id,
                        run_id = run.id
                    )

                    print(run.status)
                    time.sleep(20)
                print(run.status)
                messages = client.beta.threads.messages.list( thread_id = thread.id)

                assistant_response = ''
                for each in messages:
                    if each.role == "assistant":  # Check for assistant role
                        assistant_response += each.role + ":" + each.content[0].text.value + "\n"  # Add newline for better readability

                st.write("Run completed!")
                st.text_area("Assistant Response", assistant_response, height=300)
                



def check_usage_limit():
    # Placeholder function to check usage limit
    # Replace with actual implementation to check usage limit from OpenAI API
    return 1  # Assume usage limit is not zero for this example

if __name__ == "__main__":
    main()
