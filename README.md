# ML-Service

ML-Service is a repository created for the purpose of extracting and summarizing characters from .epub files. It includes two additional programs:

- **Span Insertion**: This program is designed to enclose character names with HTML spans inside .epub files, enabling character names to be highlighted in the front-end prototype.

- **Evaluation Program**: The Evaluation Program allows for the manual insertion of a reference and a candidate string. This facilitates the evaluation of the summary using BERTScore metrics such as F1, Recall, and Precision.

## Note

- In the `character_extraction.ipynb` notebook, the books are hardcoded and need to be adjusted accordingly.
- In the `character_summarization.ipynb` notebook, the books are hardcoded and need to be adjusted. Additionally, when summarizing a range of characters, the range has to be manually inserted in the extract chunks section.

## Project Setup
Ensure all commands are executed from the project root.

1. **Environment Setup**: Create and activate a virtual environment.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2. **Install Dependencies**: Install all required dependencies.
    ```bash
    pip install -r requirements.txt
    ```

3. **Run Tests**: Execute all tests (requires Docker to run locally).
    ```bash
    pytest
    ```
