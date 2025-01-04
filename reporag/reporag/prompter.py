# repoprompter/repoprompter/prompter.py
def create_prompt(structured_text):
    prompt = f"""
    The following is the content of a GitHub repository converted into text format. The repository contains various files and directories, each serving a specific purpose. Please analyze and understand the content of this repository.

    Repository Content:
    {structured_text}

    Instructions:
    1. Identify the main purpose of the repository.
    2. Summarize the key functionalities provided by the repository.
    3. Highlight any important files or directories and their roles.
    4. Note any dependencies or requirements specified in the repository.
    5. Provide any additional insights or observations about the repository's structure and content.

    Please provide a detailed analysis based on the above instructions.
    """
    return prompt