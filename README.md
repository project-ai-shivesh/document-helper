# LangChain Documentation Helper

## Setup with UV

This project uses [UV](https://github.com/astral-sh/uv) for dependency management.

### Installation

First, ensure you have UV installed. Then, to set up the project:

```bash
uv sync
```

This will create a virtual environment and install all dependencies.

### Running the project

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Or use UV to run commands directly:

```bash
uv run python ingestion.py
```

## Ingestion Flow

The document ingestion pipeline follows a structured process to crawl, process, and index LangChain documentation. Below is the activity diagram and key code snippets for each step.

### Activity Diagram

```mermaid
flowchart TD
    A[🚀 Start Ingestion Pipeline] --> B[Load Environment Variables]
    B --> C[Configure SSL Context]
    C --> D[Initialize Components]
    D --> E[Crawl Documentation Site]
    
    E --> F{Response Type?}
    F -->|String Error| G[Log Error & Exit]
    F -->|Dict Success| H[Convert to Document Objects]
    
    H --> I[Split Documents into Chunks]
    I --> J[Index Documents Asynchronously]
    J --> K[Process in Batches]
    
    K --> L{All Batches Successful?}
    L -->|Yes| M[Log Success Summary]
    L -->|No| N[Log Partial Success]
    
    M --> O[🎉 Pipeline Complete]
    N --> O
    G --> P[❌ Pipeline Failed]
```

### Key Components Initialization

```python
# Load environment variables
load_dotenv()

# Configure SSL Context to use certifi's certificates CA Bundle
ssl_context = ssl.create_default_context(cafile=certifi.where())
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# Initialize core components
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    show_progress_bar=False,
    chunk_size=50,
    retry_min_seconds=10,
)

vectorstore = PineconeVectorStore(index_name="langchain-doc-index", embedding=embeddings)
tavily_crawl = TavilyCrawl()
```

### Documentation Crawling

```python
# Crawl the documentation site
res = tavily_crawl.invoke({
    "url": "https://python.langchain.com/",
    "max_depth": 2,
    "extract_depth": "advanced",
})

# Convert Tavily crawl results to LangChain Document Objects
all_docs = []
for tavily_crawl_result_item in res["results"]:
    all_docs.append(
        Document(
            page_content=tavily_crawl_result_item["raw_content"],
            metadata={"source": tavily_crawl_result_item["url"]},
        )
    )
```

### Document Chunking

```python
# Split document into Chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
splitted_docs = text_splitter.split_documents(all_docs)
```

### Asynchronous Vector Indexing

```python
async def index_documents_async(documents: List[Document], batch_size: int = 50):
    """Process Documents in batches and Asynchronously."""
    
    # Create Batches
    batches = [
        documents[i : i + batch_size] for i in range(0, len(documents), batch_size)
    ]
    
    # Process all batches Concurrently
    async def add_batch(batch: List[Document], batch_num: int):
        try:
            await vectorstore.aadd_documents(batch)
            return True
        except Exception as e:
            log_error(f"VectorStore Indexing: Failed to add batch {batch_num} - {e}")
            return False
    
    # Process batches Concurrently
    tasks = [add_batch(batch, i + 1) for i, batch in enumerate(batches)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Count successful batches
    successful = sum(1 for result in results if isinstance(result, bool) and result)
    
    return successful, len(batches)
```

### Pipeline Execution

```python
async def main():
    """Main async function to orchestrate the entire process."""
    log_header("🚀 Starting LangChain Documentation Helper")
    
    # ... initialization code ...
    
    # Crawl and process documents
    res = tavily_crawl.invoke({
        "url": "https://python.langchain.com/",
        "max_depth": 2,
        "extract_depth": "advanced",
    })
    
    # Convert to documents and split
    all_docs = [Document(page_content=item["raw_content"], 
                        metadata={"source": item["url"]}) 
               for item in res["results"]]
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
    splitted_docs = text_splitter.split_documents(all_docs)
    
    # Index asynchronously
    await index_documents_async(splitted_docs, batch_size=500)
    
    log_header("PIPELINE COMPLETE")
    log_success("🎉 All documents have been processed and indexed successfully!")
```

## RAG Implementation Flow

The Retrieval-Augmented Generation (RAG) pipeline enables intelligent question-answering over the indexed LangChain documentation. Below is the activity diagram and key code snippets for the RAG implementation.

### Activity Diagram

```mermaid
flowchart TD
    A[🔍 User Query] --> B[Initialize RAG Components]
    B --> C[Create Retrieval Tool]
    C --> D[Build Agent with Tool]
    
    D --> E[Process Query through Agent]
    E --> F[Agent Decides to Use Tool]
    F --> G[Execute Retrieval Tool]
    
    G --> H[Search Vector Store]
    H --> I[Retrieve Top-K Documents]
    I --> J[Serialize Documents]
    
    J --> K[Return Context to Agent]
    K --> L[Agent Generates Answer]
    L --> M[Extract Final Answer]
    
    M --> N[Extract Context Documents]
    N --> O[Return Answer + Context]
    
    F -->|No Tool Needed| L
```

### Core Components Initialization

```python
# Load environment variables
load_dotenv()

# Initialize Embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Initialize Vector Store
vectorstore = PineconeVectorStore(index_name="langchain-doc-index", embedding=embeddings)

# Initialize Chat Model
model = init_chat_model("gpt-5.2", model_provider="openai")
```

### Retrieval Tool Implementation

```python
@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve relevant documentation to help answer queries about LangChain."""
    
    # Retrieve top 4 similar documents
    retrieved_docs = vectorstore.as_retriever().invoke(query, k=4)
    
    # Serialize documents for the model
    serialized = "\n\n".join(
        (f"Source: {doc.metadata.get('source', 'Unknown')}\n\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    
    # Return both serialized content and raw documents
    return serialized, retrieved_docs
```

### Agent Creation and Configuration

```python
def run_llm(query: str) -> Dict[str, Any]:
    """
    Run the RAG pipeline to answer a query using retrieved documentation.
    """
    
    # Create the agent with retrieval tool
    system_prompt = (
        "You are a helpful AI assistant that answers questions about LangChain documentation. "
        "You have access to a tool that retrieves relevant documentation. "
        "Use the tool to find relevant information before answering questions. "
        "Always cite the sources you use in your answers. "
        "If you cannot find the answer in the retrieved documentation, say so."
    )
    
    agent = create_agent(model, tools=[retrieve_context], system_prompt=system_prompt)
    
    # Build message list
    messages = [{"role": "user", "content": query}]
    
    # Invoke the agent
    response = agent.invoke({"messages": messages})
    
    # Extract the answer from the last AIMessage
    answer = response["messages"][-1].content
    
    # Extract context documents from ToolMessage artifacts
    context_docs = []
    for message in response["messages"]:
        if isinstance(message, ToolMessage) and hasattr(message, "artifact"):
            if isinstance(message.artifact, list):
                context_docs.extend(message.artifact)
    
    return {
        "answer": answer,
        "context": context_docs
    }
```

### RAG Pipeline Execution

```python
if __name__ == "__main__":
    # Example usage
    query = "What are deep agents?"
    result = run_llm(query=query)
    
    print("Answer:", result["answer"])
    print("\nContext Documents:")
    for i, doc in enumerate(result["context"], 1):
        print(f"{i}. Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"   Content: {doc.page_content[:200]}...")
        print()
```

### Key Features

- **Intelligent Retrieval**: Uses semantic similarity to find the most relevant documentation chunks
- **Tool-Augmented Agent**: Leverages LangChain's agent framework with custom retrieval tools
- **Source Attribution**: Always cites sources and provides context documents
- **Error Handling**: Gracefully handles cases where information isn't found
- **Structured Output**: Returns both the answer and supporting context documents

### Usage Example

```python
# Query the RAG system
result = run_llm("How do I create a custom agent in LangChain?")

# Access the generated answer
answer = result["answer"]

# Access the source documents used for generation
context_documents = result["context"]
```

This RAG implementation provides accurate, contextually-rich answers to questions about LangChain by retrieving relevant documentation chunks and using them to inform the AI's responses.
