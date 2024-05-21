
# TESTING

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
import argparse

# CLI Arguments
parser = argparse.ArgumentParser(description='Short sample app')
parser.add_argument('--path', action="store", dest='path', default=0)
args = parser.parse_args()

# Individual arguments can be accessed as attributes...
print(args.path)


# Load Data

print("Loading Data")

documents = SimpleDirectoryReader(args.path).load_data()

# nomic embedding model
Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")

# ollama
Settings.llm = Ollama(model="llama3", request_timeout=360.0)



print("Creating Index")
index = VectorStoreIndex.from_documents(
    documents,
)


print("Querying")
query_engine = index.as_query_engine()
response = query_engine.query("What file would I add a view for the /portal/ files? What file defines the urls for those views?")
print(response)

# Step 1: Load Workspace As Data
#   a. Take directory from input and load all files in it.
#      i. Ignore files that are not relevant
#


# Step 2: Index Data


# Step 3: Store Data

# Step 4: Querying

# Step 5: Evaluation



