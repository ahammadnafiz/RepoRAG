# repoprompter/repoprompter/structurer.py
def structure_text_for_llm(text_content):
    structured_text = "\n".join(text_content)
    return structured_text