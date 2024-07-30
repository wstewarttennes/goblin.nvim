import os
import ast
from typing_extensions import TypedDict, List
from typing import List, Tuple
from IPython.display import Image, display
from langgraph.graph import START, END, StateGraph
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import Document
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import SKLearnVectorStore
from langchain_nomic.embeddings import NomicEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_core.tools import tool
from langchain.schema import Document

class CodebasePreprocessor:
    def __init__(self, directory_paths: List[str], file_extension: str = '.py', exclude_dirs: List[str] = []):
        self.directory_paths = directory_paths
        self.file_extension = file_extension
        self.exclude_dirs = {os.path.abspath(d) for d in exclude_dirs}

    def extract_functions_and_classes(self, code: str) -> List[Tuple[str, str]]:
        tree = ast.parse(code)
        extracted = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                start_lineno = node.lineno
                end_lineno = node.end_lineno if hasattr(node, 'end_lineno') else node.body[-1].lineno
                extracted.append((node.name, "\n".join(code.splitlines()[start_lineno-1:end_lineno])))
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
                extracted.append(("docstring", node.value.s))
                
        return extracted

    def preprocess_codebase(self) -> List[Tuple[str, str]]:
        extracted_elements = []
        for directory_path in self.directory_paths:
            for root, _, files in os.walk(directory_path):
                abs_root = os.path.abspath(root)
                if any(abs_root.startswith(exclude_dir) for exclude_dir in self.exclude_dirs):
                    continue
                for file in files:
                    if file.endswith(self.file_extension):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                code = f.read()
                        except UnicodeDecodeError:
                            print(f"Skipping file due to encoding error: {file_path}")
                            continue
                        extracted_elements.extend(self.extract_functions_and_classes(code))
        return extracted_elements

class CustomCodebaseLoader:
    def __init__(self, directory_paths: List[str], file_extension: str = '.py', exclude_dirs: List[str] = []):
        self.preprocessor = CodebasePreprocessor(directory_paths, file_extension, exclude_dirs)

    def load(self) -> List[Document]:
        processed_elements = self.preprocessor.preprocess_codebase()
        documents = []
        for name, content in processed_elements:
            documents.append(Document(page_content=content, metadata={"name": name}))
        return documents# Initialize the custom loader with the path to your codebase

DIRECTORIES_TO_PROCESS = ["."]
DIRECTORIES_TO_EXCLUDE = ["./python/venv"]

codebase_loader = CustomCodebaseLoader(DIRECTORIES_TO_PROCESS, exclude_dirs=DIRECTORIES_TO_EXCLUDE)

# Load the documents
documents = codebase_loader.load()
for document in documents:
    print(document)

# Initialize a text splitter with specified chunk size and overlap
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=250, chunk_overlap=0
)

# Split the documents into chunks
doc_splits = text_splitter.split_documents(documents)

# Add the document chunks to the "vector store" using NomicEmbeddings
vectorstore = SKLearnVectorStore.from_documents(
    documents=doc_splits,
    # embedding=NomicEmbeddings(model="nomic-embed-text-v1.5", inference_mode="local"),
    embedding=OpenAIEmbeddings(),
)
retriever = vectorstore.as_retriever(k=4)

web_search_tool = TavilySearchResults()
prompt = PromptTemplate(
    template="""You are an assistant for question-answering tasks. 
    
    Use the following documents to answer the question. 
    
    If you don't know the answer, just say that you don't know. 
    
    Use three sentences maximum and keep the answer concise:
    Question: {question} 
    Documents: {documents} 
    Answer: 
    """,
    input_variables=["question", "documents"],
)

llm = ChatOllama(
    model="llama3.1",
    temperature=0,
)

rag_chain = prompt | llm | StrOutputParser()
# JSON
llm = ChatOllama(model="llama3.1", format="json", temperature=0)


prompt = PromptTemplate(
    template="""You are a grader assessing relevance of a retrieved document to a user question. \n 
    Here is the retrieved document: \n\n {document} \n\n
    Here is the user question: {question} \n
    If the document contains keywords related to the user question, grade it as relevant. \n
    It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question. \n
    Provide the binary score as a JSON with a single key 'score' and no premable or explanation.""",
    input_variables=["question", "document"],
)

retrieval_grader = prompt | llm | JsonOutputParser()


class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        search: whether to add search
        documents: list of documents
    """

    question: str
    generation: str
    search: str
    documents: List[str]
    steps: List[str]


def retrieve(state):
    """
    Retrieve documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    question = state["question"]
    documents = retriever.invoke(question)
    steps = state["steps"]
    steps.append("retrieve_documents")
    return {"documents": documents, "question": question, "steps": steps}


def generate(state):
    """
    Generate answer

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """

    question = state["question"]
    documents = state["documents"]
    generation = rag_chain.invoke({"documents": documents, "question": question})
    steps = state["steps"]
    steps.append("generate_answer")
    return {
        "documents": documents,
        "question": question,
        "generation": generation,
        "steps": steps,
    }


def grade_documents(state):
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with only filtered relevant documents
    """

    question = state["question"]
    documents = state["documents"]
    steps = state["steps"]
    steps.append("grade_document_retrieval")
    filtered_docs = []
    search = "No"
    for d in documents:
        score = retrieval_grader.invoke(
            {"question": question, "document": d.page_content}
        )
        grade = score["score"]
        if grade == "yes":
            filtered_docs.append(d)
        else:
            search = "Yes"
            continue
    return {
        "documents": filtered_docs,
        "question": question,
        "search": search,
        "steps": steps,
    }


def web_search(state):
    """
    Web search based on the re-phrased question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with appended web results
    """

    question = state["question"]
    documents = state.get("documents", [])
    steps = state["steps"]
    steps.append("web_search")
    web_results = web_search_tool.invoke({"query": question})
    documents.extend(
        [
            Document(page_content=d["content"], metadata={"url": d["url"]})
            for d in web_results
        ]
    )
    return {"documents": documents, "question": question, "steps": steps}


def decide_to_generate(state):
    """
    Determines whether to generate an answer, or re-generate a question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """
    search = state["search"]
    if search == "Yes":
        return "search"
    else:
        return "generate"


# Graph
workflow = StateGraph(GraphState)

# Define the nodes
workflow.add_node("retrieve", retrieve)  # retrieve
workflow.add_node("grade_documents", grade_documents)  # grade documents
workflow.add_node("generate", generate)  # generatae
workflow.add_node("web_search", web_search)  # web search

# Build graph
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "search": "web_search",
        "generate": "generate",
    },
)
workflow.add_edge("web_search", "generate")
workflow.add_edge("generate", END)

custom_graph = workflow.compile()

initial_state = {
    "question": "What is Goblin?",
    "generation": "",
    "search": "No",
    "documents": [],
    "steps": []
}

def run_state_graph(workflow, initial_state, entry_point):
    current_node = entry_point
    current_state = initial_state

    while current_node != END:
        # Access the RunnableCallable object within the tuple
        node_spec = workflow.nodes[current_node]
        node_function = node_spec[0]  # Assuming the RunnableCallable object is the first element in the tuple
        current_state = node_function.invoke(current_state)  # Use invoke or the appropriate method to execute it

        # Determine the next node
        if current_node in workflow.edges:
            next_nodes = workflow.edges[current_node]
        else:
            next_nodes = []

        if callable(next_nodes):
            current_node = next_nodes(current_state)
        elif next_nodes:
            current_node = next_nodes[0]  # For simplicity, assume linear execution
        else:
            break

    return current_state

result = run_state_graph(workflow, initial_state, "retrieve")

print("Final state:", result)
print("Generated answer:", result.get("generation"))


