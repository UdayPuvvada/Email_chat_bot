from fastapi import FastAPI,Request, Header, HTTPException
from langchain_ollama import ChatOllama
import faiss
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
model = 'llama3.2:1b'
llm = ChatOllama(
                model = "llama3.2:1b",
                temperature = 0.8,
                num_predict = 256)


app = FastAPI()
embeddings = OllamaEmbeddings(model='nomic-embed-text', base_url='http://localhost:11434')
vectorstore = FAISS.load_local(
    folder_path="Vector_DB",
    embeddings=embeddings,
    allow_dangerous_deserialization=True  # Required after LangChain v0.1.13+
)
def retreiver(question):
    docs = vectorstore.search(query=question, k=1, search_type="similarity") 
    return '\n\n'.join([doc.page_content for doc in docs])


def main():
    #if x_api_key != "generate_x_068_super_8034_Uday_Auth":
        #raise HTTPException(status_code=401, detail="Unauthorized")
    question="Did I get any Job placement offers?"
    context=retreiver(question)
    prompt = f"""
    You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know.
    Answer in bullet points. Make sure your answer is relevant to the question and it is answered from the context only.
    Question: {question}
    Context: {context} 
    Answer:
    """

   
    result=llm.invoke(prompt)
    print(result.content)

if __name__ == "__main__":
    main()
    

    


