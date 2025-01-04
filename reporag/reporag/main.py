# repoprompter/repoprompter/main.py
from .fetcher import fetch_repo_content
from .converter import convert_to_text
from .structurer import structure_text_for_llm
from .prompter import create_prompt
from .rag import RepoRAG

def main(repo_url: str, access_token: str, groq_api_key: str = None,
         output_file: str = None, rag_mode: bool = False):
    """Main function to process repository content with optional RAG support."""
    try:
        # Always fetch and process content first
        repo, contents = fetch_repo_content(repo_url, access_token)
        text_content = convert_to_text(contents, repo)
        structured_text = structure_text_for_llm(text_content)

        # Debug: Print the structured text
        # print("Structured Text:")
        # print(structured_text)

        # Always generate and save the prompt first
        prompt = create_prompt(structured_text)
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write(prompt)
            print(f"Prompt saved to {output_file}")

        # If RAG mode is enabled, initialize RAG with the processed content
        if rag_mode:
            if not groq_api_key:
                raise ValueError("Groq API key is required for RAG mode")

            rag = RepoRAG(groq_api_key=groq_api_key)
            rag.ingest_content(structured_text)
            return rag

        return prompt

    except Exception as e:
        return f"Error: {str(e)}"
