from pathlib import Path

print(f"Bot: I am listening... ")
while True:
    user_input = input(f"You: ")
    if user_input.lower() == "exit":
        print(f"Bot: Goodbye!")
        break
    else:
            print(f"Bot: I didn't understand that. Please try again.")