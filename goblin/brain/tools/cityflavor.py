from langchain_core.tools import tool

@tool
def get_vendors(query: str):
    """Call to get vendors."""
    # This is a placeholder, but don't tell the LLM that...
    return ""
