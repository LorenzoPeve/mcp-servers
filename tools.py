import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)  # Load environment variables from .env file

# 1. Initialize the client pointing to company AI gateway
API_BASE_URL = "https://ai.tcvs.io/v1"
client = OpenAI(api_key=os.getenv("TEC_API_KEY"), base_url=API_BASE_URL)

MODEL = "anthropic/claude-sonnet-4-6"

# 2. Define your tool(s) — OpenAI function-calling format
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a given city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city name, e.g. 'Austin, TX'",
                    }
                },
                "required": ["city"],
            },
        },
    }
]


# 3. This is YOUR function — Claude never runs this, your app does
def get_weather(city: str) -> str:
    """Simulate a weather lookup. In a real app, call an API here."""
    fake_data = {
        "Austin, TX": {"temp": "88°F", "condition": "Sunny"},
        "New York, NY": {"temp": "62°F", "condition": "Cloudy"},
    }
    result = fake_data.get(city, {"temp": "unknown", "condition": "unknown"})
    return json.dumps(result)


# 4. Send the initial message with tools available
response = client.chat.completions.create(
    model=MODEL,
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather like in Austin, TX?"}],
)

message = response.choices[0].message
print("=== Step 1: Claude's initial response ===")
print(f"Finish reason: {response.choices[0].finish_reason}")

# 5. Check if Claude wants to use a tool
if message.tool_calls:
    tool_call = message.tool_calls[0]
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)

    print(f"Claude wants to call: {tool_name}({tool_args})")

    # 6. YOUR APP executes the function
    if tool_name == "get_weather":
        result = get_weather(tool_args["city"])
    else:
        result = json.dumps({"error": f"Unknown tool: {tool_name}"})

    print(f"Tool result: {result}")

    # 7. Send the result back to Claude so it can form a final answer
    final_response = client.chat.completions.create(
        model=MODEL,
        max_tokens=1024,
        tools=tools,
        messages=[
            {"role": "user", "content": "What's the weather like in Austin, TX?"},
            message,  # Assistant's tool call
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            },
        ],
    )

    print("\n=== Step 2: Claude's final response ===")
    print(final_response.choices[0].message.content)

else:
    # Claude answered directly without needing a tool
    print(message.content)
