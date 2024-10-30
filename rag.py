from langchain.chains import (
    create_history_aware_retriever,
    create_retrieval_chain,
)
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

import os
from dotenv import load_dotenv
from langchain import hub
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.embeddings.spacy_embeddings import SpacyEmbeddings
from langchain_groq import ChatGroq
from pymupdf4llm import to_markdown
from typing import List, Dict, Any



class Document:
    def __init__(self, page_content: str, metadata: Dict[str, Any]):
        self.page_content = page_content
        self.metadata = metadata

    def __repr__(self):
        return f"Document(page_content={repr(self.page_content)}, metadata={self.metadata})"

def llamaindex_to_langchain(llamaindex_output: List[Dict[str, Any]]) -> List[Document]:
    langchain_output = []

    for item in llamaindex_output:
        # Extract the text content and metadata from the LlamaIndex dictionary
        text = item["text"]
        metadata = item["metadata"]

        # Transform the metadata to match the LangChain structure
        langchain_metadata = {
            "source": metadata["file_path"],
            "file_path": metadata["file_path"],
            "page": metadata["page"],
            "total_pages": metadata["page_count"],
            "format": metadata["format"],
            "title": metadata["title"],
            "author": metadata["author"],
            "subject": metadata["subject"],
            "keywords": metadata["keywords"],
            "creator": metadata["creator"],
            "producer": metadata["producer"],
            "creationDate": metadata["creationDate"],
            "modDate": metadata["modDate"],
            "trapped": metadata["trapped"],
        }

        # Create a new Document object for the LangChain output
        document = Document(page_content=text, metadata=langchain_metadata)
        langchain_output.append(document)

    return langchain_output



class RAGModule:
    def __init__(self, pdf_path="docs/cv.pdf"):
        load_dotenv()
        
        # Initialize components
        #self.loader = PyPDFLoader(pdf_path)
        #self.document = self.loader.load()
        self.loader = to_markdown(pdf_path, page_chunks=True, write_images=False)
        self.document = llamaindex_to_langchain(self.loader)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.splits = self.text_splitter.split_documents(self.document)
        self.vectorstore = Chroma.from_documents(documents=self.splits, embedding=FastEmbedEmbeddings())
        self.retriever = self.vectorstore.as_retriever()
        
        self.llm = ChatGroq(
            model="llama-3.2-1b-preview",
            temperature=0.6,
            max_tokens=300,
            api_key=os.getenv("GROQ_API_KEY"),
        )
        
        # Set up the chain
        self.setup_chain()
        
    def setup_chain(self):
        # Contextualize question
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, just "
            "reformulate it if needed and otherwise return it as is."
        )
        
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, contextualize_q_prompt
        )
        
        """qa_system_prompt = (
            "You are an assistant for question-answering tasks. Your responses "
            "should be related to the data scientist Moudathirou Ben Saindou, "
            "and based on his provided CV, which is attached. Use the following "
            "pieces of retrieved context to answer the question. If you don't know "
            "the answer, just say that you don't know. Use three sentences maximum "
            "and keep the answer concise."
            "{context}"
        )"""

        qa_system_prompt = (
        "You are an assistant for question-answering tasks aimed at promoting Moudathirou Ben Saindou "
        "to potential recruiters and interested parties. Your responses should be persuasive and highlight "
        "his strengths as a data scientist, based on his provided CV. If contact information like phone "
        "numbers or email addresses are requested and present in the CV, provide them, as their inclusion "
        "in the CV implies consent to share. Use the following pieces of retrieved context to answer "
        "questions. Focus on selling his skills, experience, and achievements while keeping responses "
        "concise with three sentences maximum. If you don't know the answer, just say that you don't know. "
        "{context}"
    )

        
        
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        
        self.rag_chain = create_retrieval_chain(
            history_aware_retriever, question_answer_chain
        )
    
    def get_response(self, user_message, chat_history):
        return self.rag_chain.invoke({
            "input": user_message,
            "chat_history": chat_history
        })