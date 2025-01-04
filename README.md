<h1 align="center">RepoRAG</h1>

![Banner](assets/banner.png)


A fully interactive tool designed to streamline your GitHub repository prompt generation process and facilitate RAG (Retrieval-Augmented Generation) workflows

---

## 🏗️ System Design & Architecture
- Below is the high-level architecture of the system:
![Flow](assets/reporagai_2.jpeg)
![Architecture](assets/reporagai_1.jpeg)


## 📌 Table of Contents
- [🌟 Features](#-features)
- [🛠️ Installation](#️-installation)
- [🚀 Usage](#-usage)
- [⚙️ Configuration](#%EF%B8%8F-configuration)
- [📖 Interactive Commands](#-interactive-commands)
- [🎨 Icons and Badges](#-icons-and-badges)
- [🧪 Example](#-example)
- [🤖 Technologies Used](#-technologies-used)
- [📃 License](#-license)
- [🤝 Contributing](#-contributing)
- [🔗 Links](#-links)
- [📝 Author](#-author)

---

## 🌟 Features
- **Interactive Mode**: Easily input repository details and start generating prompts through a user-friendly interface.
- **RAG Support**: Engage in interactive Retrieval-Augmented Generation sessions with real-time question answering about your repositories.
- **Environment Variable Management**: Supports environment-based configurations for quick and seamless setup.
- **Error Handling**: Robust error handling to ensure smooth operations during interactive sessions.
- **Clear Command Interface**: Offers a set of easy-to-use commands for RAG sessions, including options to clear history or exit the session.

---

## 🛠️ Installation

Follow these steps to get started with RepoRAG:

1. **Clone the repository**:
```bash
$ git clone https://github.com/ahammadnafiz/RepoRAG.git
```

2. **Navigate to the project directory**:
```bash
$ cd RepoRAG
```

3. **Install the required dependencies**:
```bash
$ pip install -r requirements.txt
```

4. **Create a `.env` file** to store your environment variables (see [Configuration](#%EF%B8%8F-configuration)).

---

## 🚀 Usage

Run the interactive mode directly from your terminal:
```bash
$ python reporag.py
```

### 🧑‍💻 Interactive Session Walkthrough:
- **Step 1**: Enter the repository URL in the format `owner/repo`.
- **Step 2**: Provide your GitHub access token.
- **Step 3**: Specify the output file name for the generated prompt.
- **Step 4**: Choose the desired mode:
  - `1`: Generate a prompt file only.
  - `2`: Generate a prompt file and start a RAG session.

---

## ⚙️ Configuration

Create a `.env` file in the root directory to store your environment variables:
```env
GITHUB_ACCESS_TOKEN=your_github_token
GROQ_API_KEY=your_groq_api_key
```

**Environment Variables Explained**:
- `GITHUB_ACCESS_TOKEN`: Your personal GitHub token for accessing private repositories.
- `GROQ_API_KEY`: API key required for advanced RAG functionalities.

---

## 📖 Interactive Commands
When running in RAG mode, you can use the following commands:

| Command | Description                    |
| ------- | ------------------------------ |
| `exit`  | Exit the RAG session           |
| `help`  | Display available commands     |
| `clear` | Clear the conversation history |

---

## 🎨 Icons and Badges

![Python](https://img.shields.io/badge/python-v3.8%2B-blue) ![GitHub](https://img.shields.io/badge/github-RepoRAG-lightgrey)

**Supported Technologies**:
- Python 3.8+
- GitHub API
- dotenv for environment variable management

---

## 🧪 Example

```bash
=== RepoRAG Interactive Mode ===

Enter the GitHub repository URL (format: owner/repo): ahammadnafiz/RepoRAG
GitHub access token not found in .env. Please enter your token: ********
Enter the output file name for the prompt (e.g., output_prompt.txt): my_prompt.txt
Available modes:
1. Generate prompt file only
2. Generate prompt file and start RAG mode
Enter your choice (1/2): 2
```

---

## 🤖 Technologies Used
- **Python**: Core language for the tool.
- **dotenv**: For environment variable management.
- **Typing**: Used for type hints and validation.
- **GitHub API**: To interact with GitHub repositories.

---

## 📃 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

We welcome contributions to RepoRAG! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add your feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Create a pull request.