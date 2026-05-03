import asyncio
import ssl
import os
import ssl
from typing import Any, Dict, List

import certifi
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
#from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_tavily import TavilyCrawl, TavilyExtract, TavilyMap

from logger import (Colors, log_info, log_success, log_warning, log_error, log_header)


# Load environment variables
load_dotenv()

# Configure SSL Context to use certifi's certificates CA Bundle
ssl_context = ssl.create_default_context(cafile=certifi.where())
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small", show_progress_bar=False, chunk_size=50, retry_min_seconds=10
)

#chroma = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
vectorstore = PineconeVectorStore(index_name="langchain-doc-index", embedding=embeddings)
tavily_extract = TavilyExtract()
tavily_map = TavilyMap(max_depth=5, max_breadth=20, max_pages=1000)
tavily_crawl = TavilyCrawl()


async def main():
    """Main async function to orchestrate the entire process."""
    log_header("🚀 Starting LangChain Documentation Helper")
    log_info("Initializing components...")
    log_success("✅ OpenAI Embeddings initialized")
    log_success("✅ Pinecone Vector Store initialized")
    log_success("✅ Tavily Extract initialized")
    log_success("✅ Tavily Map initialized")
    log_success("✅ Tavily Crawl initialized")
    log_info("All components ready! The ingestion system is prepared for document processing.")
    log_header("*"*40+"✨ Setup Complete"+"*"*40)

    log_info("DOCUMENTATION INGESTION PIPELINE")
    log_info(
        "TavilyCrawl: Starting to Crawl documentation from https://python.langchain.com/",
        Colors.PURPLE,
    )

#Crawl the documentation site
    try:
        res = tavily_crawl.invoke({
            "url": "https://python.langchain.com/",
            "max_depth": 1,
            "extract_depth": "advanced",
            "instructions": "content on ai agents"
        })

        # Check if the response is a string (error message) or dict (success)
        if isinstance(res, str):
            log_error(f"TavilyCrawl failed: {res}")
            return
        #all_docs = res["results"]
        all_docs = [Document(page_content=result['raw_content'], metadat={"source": result['url']}) for result in res["results"]]

        log_success(
            f"TavilyCrawl: Successfully crawled {len(all_docs)} documents from documentation site"
        )
        # Process the documents here
        log_info("Processing documents...")

    except Exception as e:
        log_error(f"Error during crawling: {str(e)}")
        return


if __name__ == "__main__":
    asyncio.run(main())