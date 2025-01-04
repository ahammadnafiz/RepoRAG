# repoprompter/repoprompter/converter.py
def convert_to_text(contents, repo):
    text_content = []
    for content in contents:
        if content.type == "file":
            try:
                if content.encoding is None or content.encoding == 'none':
                    raise UnicodeDecodeError("unsupported encoding", b"", 0, 1, "none")
                file_content = content.decoded_content.decode('utf-8')
                file_info = f"File: {content.path}\nSize: {content.size} bytes\nLast Modified: {content.last_modified}\nContent:\n{file_content}\n"
                text_content.append(file_info)
            except (UnicodeDecodeError, AttributeError):
                text_content.append(f"File: {content.path} (binary or non-UTF-8 content)\nSize: {content.size} bytes\nLast Modified: {content.last_modified}\n")
        elif content.type == "dir":
            dir_info = f"Directory: {content.path}\n"
            text_content.append(dir_info)
            text_content.extend(convert_to_text(repo.get_contents(content.path), repo))
    return text_content