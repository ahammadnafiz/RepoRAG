from reporag.reporag.main import main
from dotenv import load_dotenv
import os
import sys
from typing import Dict, Any, Optional

def validate_repo_url(url: str) -> bool:
    """Validate the repository URL format."""
    parts = url.split('/')
    return len(parts) == 2 and all(part.strip() for part in parts)

def get_env_or_input(env_var: str, prompt: str) -> str:
    """Get value from environment variable or user input."""
    value = os.getenv(env_var)
    if not value:
        value = input(prompt).strip()
    return value

def get_user_input() -> Dict[str, Any]:
    """Get and validate user input for repository processing."""
    print("\n=== Repoprompter Interactive Mode ===\n")

    # Get and validate repository URL
    while True:
        repo_url = input("Enter the GitHub repository URL (format: owner/repo): ").strip()
        if validate_repo_url(repo_url):
            break
        print("Invalid repository format. Please use 'owner/repo' format.")

    # Get tokens
    github_token = get_env_or_input(
        'GITHUB_ACCESS_TOKEN',
        "GitHub access token not found in .env. Please enter your token: "
    )

    # Get output file name (now required for all modes)
    while True:
        output_file = input("\nEnter the output file name for the prompt (e.g., output_prompt.txt): ").strip()
        if output_file:
            break
        print("Output file name cannot be empty.")

    # Choose mode with input validation
    while True:
        print("\nAvailable modes:")
        print("1. Generate prompt file only")
        print("2. Generate prompt file and start RAG mode")
        mode = input("Enter your choice (1/2): ").strip()
        if mode in ['1', '2']:
            break
        print("Invalid choice. Please enter 1 or 2.")

    result = {
        'repo_url': repo_url,
        'github_token': github_token,
        'output_file': output_file,
        'mode': 'prompt' if mode == '1' else 'rag'
    }

    if mode == '2':
        result['groq_token'] = get_env_or_input(
            'GROQ_API_KEY',
            "Groq API key not found in .env. Please enter your key: "
        )

    return result

def interactive_rag_session(rag_instance: Any) -> None:
    """Run an interactive RAG session with improved error handling."""
    print("\n=== RAG Interactive Mode ===")
    print("Available commands:")
    print("- exit: Exit the RAG session")
    print("- help: Show this help message")
    print("- clear: Clear the conversation history")
    print("- Any other input will be treated as a question about the repository\n")

    while True:
        try:
            question = input("\nQuestion: ").strip()

            if not question:
                print("Please enter a question or command.")
                continue

            command = question.lower()
            if command == 'exit':
                print("Exiting RAG session...")
                rag_instance.clear_vector_store()  # Clear the vector store
                rag_instance.clear_cache()  # Clear the cache
                break
            elif command == 'help':
                print("\nAvailable commands:")
                print("- exit: Exit the RAG session")
                print("- help: Show this help message")
                print("- clear: Clear the conversation history")
                print("- Any other input will be treated as a question about the repository")
                continue
            elif command == 'clear':
                rag_instance.clear_memory()
                print("Conversation history cleared.")
                continue

            print("\nProcessing your question...")
            answer = rag_instance.query(question)
            print("\nAnswer:", answer)

        except KeyboardInterrupt:
            print("\nExiting RAG session...")
            rag_instance.clear_vector_store()  # Clear the vector store
            rag_instance.clear_cache()  # Clear the cache
            break
        except Exception as e:
            print(f"\nError processing question: {str(e)}")
            print("Please try another question or type 'exit' to quit.")

def main_interactive() -> None:
    """Main interactive function with improved error handling."""
    try:
        # Load environment variables
        load_dotenv(override=True)

        # Get user inputs
        inputs = get_user_input()

        print("\nInitializing...")

        if inputs['mode'] == 'prompt':
            # Generate prompt file only
            result = main(
                repo_url=inputs['repo_url'],
                access_token=inputs['github_token'],
                output_file=inputs['output_file']
            )

            if isinstance(result, str) and result.startswith("Error"):
                raise Exception(result)

            print(f"\nPrompt successfully generated and saved to {inputs['output_file']}")

        else:
            # Generate prompt file and initialize RAG
            result = main(
                repo_url=inputs['repo_url'],
                access_token=inputs['github_token'],
                groq_api_key=inputs['groq_token'],
                output_file=inputs['output_file'],
                rag_mode=True
            )

            if isinstance(result, str) and result.startswith("Error"):
                raise Exception(result)

            print(f"\nPrompt file generated and saved to {inputs['output_file']}")
            print("RAG system initialized successfully.")

            # Start interactive RAG session
            interactive_rag_session(result)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please check your inputs and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main_interactive()