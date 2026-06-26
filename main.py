import os
import argparse

from dotenv import load_dotenv
from google import genai
from google.genai import types

# import constant variable from "prompts.py"
from prompts import system_prompt


def main():
    # Accept command-line argument as the 'AI prompt'
    parser = argparse.ArgumentParser(description="Chatbot")
    parser.add_argument("user_prompt", type=str, help="User prompt")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    # Now we can access `args.user_prompt`

    # Read the .env file's secret API key, using the 'dotenv' library
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key is None:
        raise RuntimeError("Gemini API key not set")

    # LLM API's work best as conversation manner, keeping track of history with each prompt
    # Therefore, create a list to store larger context of the conversation(s)
    messages: list[types.Content] = [
        types.Content(role="user", parts=[types.Part(text=args.user_prompt)])
    ]
    # Each message has a 'role', to differentiate between system's guardrails and user's prompt

    # Create a new instance variable of a Gemini client, using the 'google' library
    client = genai.Client(api_key=api_key)

    # Call the LLM model and print results
    response = generate_content(client, messages)

    # Display the response and more info, if --verbose CLI argument was given
    print_conversation(request=args.user_prompt, response=response, is_verbose=args.verbose)

def generate_content(client: genai.Client, messages: list[types.Content] ):
    # Get a response from gemini-2.5-flash-model
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        #contents="Why is Boot.dev such a great place to learn backend development? Use one paragraph maximum."
        #contents=args.user_prompt,
        contents=messages,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0,
        ),
    )
    # Verify response's 'usage_metadata' property is given
    if response.usage_metadata is None:
        raise RuntimeError("Model response metadata not given by API")

    if response.usage_metadata.prompt_token_count is None:
        raise RuntimeError("Number of tokens of the prompt sent to the model is not given by API")

    if response.usage_metadata.candidates_token_count is None:
        raise RuntimeError("Number of tokens in model's response is not given by API")

    return response

def print_conversation(request, response, is_verbose) -> None:
    # Print number of tokens consumed by this model interaction
    if is_verbose:
        print(f"User prompt: {request}")
        print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
        print(f"Response tokens: {response.usage_metadata.candidates_token_count}")

    # Print the response from Gemini's model
    print(response.text)

if __name__ == "__main__":
    main()
