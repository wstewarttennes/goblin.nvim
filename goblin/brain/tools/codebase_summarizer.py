import os
import glob
from typing import List, Dict
from pathlib import Path
import tiktoken
import openai
from collections import defaultdict
from tqdm import tqdm

class CodebaseSummarizer:
    def __init__(self):
        """Initialize the summarizer with OpenAI API key."""
        openai.api_key = os.environ.get("OPENAI_API_KEY") 
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.max_tokens = 8000  # Safe limit for GPT-4
        self.ignored_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.env'}
        self.code_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c',
            '.html', '.css', '.sql', '.go', '.rs', '.rb', '.php'
        }

    def read_file(self, file_path: str) -> str:
        """Read a file and return its contents."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def should_process_file(self, file_path: str) -> bool:
        """Determine if a file should be processed based on extension and path."""
        path_parts = Path(file_path).parts
        return (any(file_path.endswith(ext) for ext in self.code_extensions) and
                not any(ignored in path_parts for ignored in self.ignored_dirs))

    def get_files_content(self, directory: str) -> Dict[str, str]:
        """Get contents of all relevant files in the directory."""
        files_content = {}
        for file_path in glob.glob(f"{directory}/**/*", recursive=True):
            if os.path.isfile(file_path) and self.should_process_file(file_path):
                relative_path = os.path.relpath(file_path, directory)
                content = self.read_file(file_path)
                if content:
                    files_content[relative_path] = content
        return files_content

    def chunk_content(self, content: str, max_tokens: int = 1000) -> List[str]:
        """Split content into chunks that don't exceed max_tokens."""
        chunks = []
        current_chunk = []
        current_length = 0
        
        lines = content.split('\n')
        for line in lines:
            line_length = len(self.encoding.encode(line))
            if current_length + line_length > max_tokens:
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_length = line_length
            else:
                current_chunk.append(line)
                current_length += line_length
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        return chunks

    def summarize_chunk(self, chunk: str) -> str:
        """Summarize a chunk of code using GPT-4."""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a technical expert who summarizes code. Be concise but comprehensive."},
                    {"role": "user", "content": f"Please summarize this code section:\n\n{chunk}"}
                ],
                max_tokens=500,
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error summarizing chunk: {str(e)}"

    def generate_file_summary(self, file_path: str, content: str) -> str:
        """Generate a summary for a single file."""
        chunks = self.chunk_content(content)
        chunk_summaries = []
        
        for chunk in tqdm(chunks, desc=f"Summarizing {file_path}", leave=False):
            summary = self.summarize_chunk(chunk)
            chunk_summaries.append(summary)
        
        # Combine chunk summaries into a file summary
        combined_summary = "\n".join(chunk_summaries)
        return self.summarize_chunk(f"File summaries for {file_path}:\n{combined_summary}")

    def generate_codebase_summary(self, directory: str) -> str:
        """Generate a complete summary of the codebase."""
        print(f"Analyzing codebase in {directory}...")
        files_content = self.get_files_content(directory)
        
        if not files_content:
            return "No code files found in the specified directory."
        
        # Group files by directory
        dir_files = defaultdict(list)
        for file_path in files_content:
            dir_name = os.path.dirname(file_path) or 'root'
            dir_files[dir_name].append(file_path)
        
        # Generate summaries for each file
        summaries = []
        for dir_name, files in dir_files.items():
            summaries.append(f"\n## Directory: {dir_name}")
            for file_path in tqdm(files, desc=f"Processing {dir_name}"):
                file_summary = self.generate_file_summary(file_path, files_content[file_path])
                summaries.append(f"\n### {file_path}\n{file_summary}")
        
        # Generate overall summary
        all_summaries = "\n".join(summaries)
        final_summary = self.summarize_chunk(
            f"Please provide a high-level summary of this entire codebase:\n{all_summaries}"
        )
        
        return f"""# Codebase Summary

## Overall Summary
{final_summary}

## Detailed Summaries by Directory
{all_summaries}
"""

from langchain_core.tools import tool

@tool
def codebase_summarizer(codepath: str, outputpath: str):
    
    summarizer = CodebaseSummarizer()
    summary = summarizer.generate_codebase_summary(codepath)
    
    with open(outputpath, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"\nSummary has been written to {outputpath}")


