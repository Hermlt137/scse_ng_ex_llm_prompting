## Import the necessary modules
import json
from ollama import chat

## Import the function from the module parse_data
from parse_data import load_items, get_unclaimed_items, save_result


## Build your prompt based on the description the user provides 
## and the items that are available in the lost-and-found database.
## The model must follow the rules listed in the README file
## The function should return the system prompt and the user prompt.
## You may need to use json.dumps() to convert the available_items list into a JSON string.

def build_prompt(description, available_items):
    system_prompt = """You are a campus lost-and-found assistant.
Your job is to find all the possible matches for the item a user lost.
Use ONLY the items given in the available items list.
Not all the details of an item must match to be a possible match.
You must return ONLY JSON with exactly the following structure:
{
    "matches": ["ITEM_ID"],
    "confidence": "LOW"
}
Rules:
- "matches" contains all the possible matches.
- "confidence" measures how confident you are about the matches.
- "confidence" must be exactly one of: LOW, MEDIUM, HIGH.
- If there is no match, return an empty list for "matches".
- Do not include any conversational filler, markdown formatting blocks, or extra text."""

    user_prompt = f"""Available items:
{json.dumps(available_items, indent=2)}

Item description: {description}

Find all the possible matches."""

    return system_prompt, user_prompt
    

## Logic to ask Qwen for all the possible matches based on the system prompt and user prompt.
## The function should return the response from Qwen.
def ask_qwen(system_prompt, user_prompt):
    response = chat(
        model="qwen3:8b",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )
    return response.message.content


## Logic to parse the response from Qwen and return the result. 
## You may need to use json.loads() to convert the response string into a suitable Python data structure.
def parse_response(response_text):
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        print("The model did not return a valid JSON response.")
        return None
    return result
    


## Logic to validate the result returned by Qwen.
## It should check if the result is a dictionary, contains the keys "matches" and "confidence", and that the values are of the correct type.
## If everything is correct, then it should check if the item IDs in the "matches" list are valid IDs .
def validate_result(result, available_items):
    if not isinstance(result, dict):
        return False

    if "matches" not in result or "confidence" not in result:
        return False

    if not isinstance(result["matches"], list):
        return False

    if not isinstance(result["confidence"], str):
        return False

    if result["confidence"] not in ["LOW", "MEDIUM", "HIGH"]:
        return False

    valid_ids = [item["id"] for item in available_items]
    for item_id in result["matches"]:
        if item_id not in valid_ids:
            return False

    return True


## Logic to display the matches found by Qwen in a user-friendly format.
## It should look something like this:
""" 
CAMPUS LOST-AND-FOUND ASSISTANT
==================================================

Describe the item you lost: I lost a black bag somewhere

Searching for possible matches...

MATCH RESULT
--------------------------------------------------
Confidence: MEDIUM

Possible matches:

ID: F101
Item: backpack
Color: black
Location: Library 2nd floor
Date found: 2026-09-15

Result saved to output/match_result.json
 """
## If no matches are found, it should display a message indicating that no matches were found, along with the empty list
def display_matches(result, available_items):
    print("MATCH RESULT")
    print("-" * 50)
    print(f"Confidence: {result['confidence']}")
    print()

    if len(result["matches"]) == 0:
        print("No possible matches were found.")
        print(f"Matches: {result['matches']}")
        return

    print("Possible matches:")
    for item_id in result["matches"]:
        for item in available_items:
            if item["id"] == item_id:
                print()
                print(f"ID: {item['id']}")
                print(f"Item: {item['item']}")
                print(f"Color: {item['color']}")
                print(f"Location: {item['location']}")
                print(f"Date found: {item['date']}")
    


## Control center for the entire program.
def main():
    print("CAMPUS LOST-AND-FOUND ASSISTANT")
    print("=" * 50)
    print()

    description = input("Describe the item you lost: ")
    print()
    print("Searching for possible matches...")

    items = load_items("found_items.json")
    available_items = get_unclaimed_items(items)

    system_prompt, user_prompt = build_prompt(description, available_items)
    response_text = ask_qwen(system_prompt, user_prompt)
    result = parse_response(response_text)

    if result is None or not validate_result(result, available_items):
        print("The result returned by the model is invalid. Please try again.")
        return

    print()
    display_matches(result, available_items)

    save_result(result, "output/match_result.json")
    print()
    print("Result saved to output/match_result.json")


if __name__ == "__main__":
    main()
