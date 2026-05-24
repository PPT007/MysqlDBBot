from utils.style import GREEN, YELLOW, RESET
from db.schema_generator import generate_schema

print(f"{YELLOW}Bot: I am listening... Type \"generate schema\" to generate a fresh schema.{RESET}")
while True:
    user_input = input(f"{GREEN}You: ")
    print(RESET, end="")
    if user_input.lower() == "exit":
        print(f"{YELLOW}Bot: Goodbye!{RESET}")
        break
    elif "generate schema" in user_input.lower():
        print(f"{YELLOW}Bot: Generating schema...{RESET}")
        generate_schema()
        print(f"{YELLOW}Bot: Schema generated successfully!{RESET}")
    else:
        print(f"{YELLOW}Bot: Currently I am not able of answering that. But will be soon!{RESET}")