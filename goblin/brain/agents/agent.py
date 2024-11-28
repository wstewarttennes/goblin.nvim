from typing import List, TypedDict

class BaseAgent():

    def __init__(self, data):
        pass

    def run(self):
        pass

class GitDiff(TypedDict):
    """
    Represents a single git diff

    Attributes:
        file_path : the file path where we are changing the code
        start_line : the line where the git diff starts (old code)
        end_line : the line where the git diff ends (old code)
        generation : Code solution
    """

    file_path: str
    start_line: int 
    end_line: int 
    generation: str


class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        error : Binary flag for control flow to indicate whether test error was tripped
        messages : With user question, error messages, reasoning
        generation : Code solution
        iterations : Number of tries
    """

    error: str
    messages: List
    generation: str
    iterations: int

