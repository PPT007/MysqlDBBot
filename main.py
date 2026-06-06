from pathlib import Path

from utils.style import GREEN, YELLOW, RESET
from db.schema_generator import generate_schema
from rag.chunker import create_schema_chunks
from rag.embedder import embed_texts, save_embeddings, DEFAULT_OUTPUT_DIR
from rag.retriever import display_top_chunks, get_top_chunks

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

        print(f"{YELLOW}Bot: Creating schema chunks...{RESET}")
        chunks = create_schema_chunks()
        print(f"{YELLOW}Bot: Created {len(chunks)} schema chunks.{RESET}")

        print(f"{YELLOW}Bot: Generating embeddings...{RESET}")
        embeddings = embed_texts(chunks)
        save_embeddings(chunks, embeddings, DEFAULT_OUTPUT_DIR / "schema_embeddings.json")
        print(f"{YELLOW}Bot: Embeddings generated and saved!{RESET}")
    else:
        top_chunks = get_top_chunks(user_input)
        display_top_chunks(user_input, top_chunks)
