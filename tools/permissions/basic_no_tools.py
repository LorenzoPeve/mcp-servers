import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(
    auth_token=os.environ["ANTHROPIC_API_KEY"],
)
MODEL = "claude-sonnet-4-6"

if __name__ == "__main__":
    conversation = []

    print("Chat with Claude (type 'quit' or 'exit' to stop)")
    print("=" * 50)

    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        conversation.append({"role": "user", "content": question})

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=conversation,
        )

        answer = response.content[0].text
        conversation.append({"role": "assistant", "content": answer})
        print(f"\nAssistant: {answer}")
