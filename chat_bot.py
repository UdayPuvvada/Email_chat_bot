from fastapi import FastAPI,Request, Header, HTTPException
from langchain_ollama import ChatOllama
import faiss
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ( HumanMessagePromptTemplate,
                                    SystemMessagePromptTemplate,
                                    ChatPromptTemplate)
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough 
from langchain_core.prompts import ChatPromptTemplate

base_url = 'https:\\127.0.0.1:11434'
model = 'llama3.2:3b'
llm = ChatOllama(
                model = "llama3.2:3b",
                temperature = 0.8,
                num_predict = 256)
system= SystemMessagePromptTemplate.from_template('You are an expert at writing email replies.')
question= HumanMessagePromptTemplate.from_template('{prompt}')
template = ChatPromptTemplate([system,question])
chain= template|llm|StrOutputParser()


embeddings = OllamaEmbeddings(model='nomic-embed-text', base_url='http://localhost:11434')
vectorstore = FAISS.load_local(
    folder_path="Vector_DB",
    embeddings=embeddings,
    allow_dangerous_deserialization=True  # Required after LangChain v0.1.13+
)
def retreiver(question):
    docs = vectorstore.search(query=question, k=5, search_type="similarity") 
    return '\n\n'.join([doc.page_content for doc in docs])

st.set_page_config(page_title="Email Assistant", page_icon="📧")
st.title("📨 Email Assistant Chatbot")

st.markdown("Ask questions related to your emails fetched from Gmail and processed by your LLM-powered RAG pipeline.")

# Text input from user
user_input = st.text_input("Enter your question:", "")    
# Button to submit query
if st.button("Ask"):
    if user_input.strip() == "":
        st.warning("Please enter a question before clicking Ask.")
    else:
        # Replace with your actual FastAPI endpoint
        context=retreiver(user_input)
        print(context)
        prompt = f"""
             # Your role
              You are a brilliant expert at understanding the intent of the questioner and the crux of the question, and providing the most optimal answer to the questioner's needs from the documents you are given.


            # Instruction
            Your task is to answer the question using the following pieces of retrieved context delimited by XML tags.

            <retrieved context>
            Retrieved Context:
            {context}
            </retrieved context>


            # Constraint
             1. Think deeply and multiple times about the user's question\nUser's question:\n{question}\nYou must understand the intent of their question and provide the most appropriate answer.
             - Ask yourself why to understand the context of the question and why the questioner asked it, reflect on it, and provide an appropriate response based on what you understand.
             2. Choose the most relevant content(the key content that directly relates to the question) from the retrieved context and use it to generate an answer.
             3. Generate a concise, logical answer. When generating the answer, Do Not just list your selections, But rearrange them in context so that they become paragraphs with a natural flow. 
             4. When you don't have retrieved context for the question or If you have a retrieved documents, but their content is irrelevant to the question, you should answer 'I can't find the answer to that question in the material I have'.
             5. Use five sentences maximum. Keep the answer concise but logical/natural/in-depth."""
            # You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question.
             #If you don't know the answer, just say that you don't know.
             #Answer in bullet points. Make sure your answer is relevant to the question and it is answered from the context only.
             #Question: {question} 
             #Context: {context} 
             #Answer:
             
        result=chain.stream(prompt)
        st.write_stream(result)

            

    


