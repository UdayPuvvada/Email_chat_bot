import boto3
import faiss
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
import os
from langchain_ollama import OllamaEmbeddings
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.docstore.document import Document
# Config
bucket_name = "uday-origin-v6"
prefix = "emails/cleaned/"

# Step 1: Download all cleaned emails from S3
def download_cleaned_emails():
    s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    documents = []

    for obj in response.get('Contents', []):
        key = obj['Key']
        s3_response = s3.get_object(Bucket=bucket_name, Key=key)
        body = s3_response['Body'].read()
        documents.append(body)

   
    return documents


def prepare_vectorstore(docs):
    chunks = [Document(page_content=chunk, metadata={}) for chunk in docs]
    embeddings = OllamaEmbeddings(model='nomic-embed-text', base_url='http://localhost:11434')
    vector = embeddings.embed_query("Hello World")
    index = faiss.IndexFlatL2(len(vector))
    vector_store = FAISS(
    embedding_function=embeddings,
    index=index,
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
   )
    vector_store.add_documents(documents=chunks)
    question = "Security"
    docs = vector_store.search(query=question, k=1, search_type="similarity") 
    print(docs)
    vector_store.save_local("Vector_DB") 


if __name__ == "__main__":
    docs=download_cleaned_emails()
    prepare_vectorstore(docs)
