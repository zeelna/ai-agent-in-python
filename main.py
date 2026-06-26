import os
import argparse
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

from call_function import available_functions, call_function
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

    # Agent Loop: Call the LLM model. Wrapping the model-calling-logic in loop.
    # so the agent can iterate on a task until it's done working and has a final response for the user
    for _ in range(20):
        response = generate_content(client=client, messages=messages)
        # .candidates property: a list of model's response(s) to the last prompt (usually just one)
        if response.candidates is not None:
            # Each iteration: model is aware of all the messages and tool-requests that model has generated so far
            for candidate in response.candidates:
                if candidate.content is not None:
                    # Add all the "candidates" to the conversation history so the model can see them in future iterations
                    messages.append(candidate.content)

        generate_conversation(response=response, messages_history=messages, is_verbose=args.verbose)

        # Display the response and more info, if --verbose CLI argument was given
        result = print_conversation(request=args.user_prompt, response=response, is_verbose=args.verbose)
        if result:
            print("Final response:")
            print(result)
            return

    print("Maximum iterations reached without a final response")
    sys.exit(1)

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
            tools=[available_functions]
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


def generate_conversation(response, messages_history, is_verbose):
    function_responses = []
    for function_call in response.function_calls:
        function_call_result = call_function(function_call=function_call, verbose=is_verbose)

        if not function_call_result.parts:
            raise Exception("EXCEPTION: cannot call function - missing .parts\n")

        function_response = function_call_result.parts[0].function_response
        if function_response is None:
            raise Exception("EXCEPTION: cannot call function - missing .parts[x].function_response\n")

        response_content = function_call_result.parts[0].function_response.response
        if response_content is None:
            raise Exception("EXCEPTION: cannot call function - missing .parts[x].function_response.response\n")

        # Model must see results of function calls it makes. Append results of function calls in history of messages.
        function_responses.append(function_call_result.parts[0])

        if is_verbose:
            print(f"-> {function_call_result.parts[0].function_response.response}")
        # print(f"Calling function: {function_call.name}({function_call.args})")

    # to avoid adding empty list into the parts= argument of types.Content()
    if function_responses:
        messages_history.append(types.Content(role="user", parts=function_responses))


def print_conversation(request, response, is_verbose) -> str | None:
    # Print number of tokens consumed by this model interaction
    if not response.function_calls:
        if is_verbose:
            return (
                f"User prompt: {request}\n"
                f"Prompt tokens: {response.usage_metadata.prompt_token_count}\n"
                f"Response tokens: {response.usage_metadata.candidates_token_count}\n"
            )
        # Print the response from Gemini's model
        return response.text
    else:
        return None


if __name__ == "__main__":
    main()
