from utils.style import GREEN, YELLOW, RESET

print(f"{YELLOW}Bot: Hey! I am listening...{RESET}")
while True:
    user_input = input(f"{GREEN}You: ")
    print(RESET, end="")
    if user_input.lower() == "exit":
        print(f"{YELLOW}Bot: Goodbye!{RESET}")
        break
    print(f"{YELLOW}Bot: Currently I am not able of answering that. But will be soon!{RESET}")