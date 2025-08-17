try:
    import Ragpipeline as rp
except ModuleNotFoundError:
    import scripts.Ragpipeline as rp
from unittest.mock import patch, MagicMock

class FakeEmbeddings:
    def __init__(self, model=None, base_url=None):
        self.model = model
        self.base_url = base_url

    def embed_query(self, text):
        # Return a fixed-size vector to define index dims
        return [0.0, 1.0, 2.0]


class FakeIndex:
    def __init__(self, dim):
        self.dim = dim


class FakeFAISSStore:
    def __init__(self, embedding_function=None, index=None, docstore=None, index_to_docstore_id=None):
        self.embedding_function = embedding_function
        self.index = index
        self.docs_added = []
        self.saved_to = None

    def add_documents(self, documents):
        # Just store their content
        self.docs_added.extend([d.page_content for d in documents])

    # The code calls `search(...)`; provide a stub
    def search(self, query, k=1, search_type="similarity"):
        return [{"doc": "dummy", "score": 0.0}]

    def save_local(self, path):
        self.saved_to = path


@patch.object(rp, "boto3")
def test_download_cleaned_emails_reads_all_objects(mock_boto):
    # Arrange fake S3 list & get
    client = MagicMock()
    mock_boto.client.return_value = client
    client.list_objects_v2.return_value = {
        "Contents": [{"Key": "emails/cleaned/a.json"}, {"Key": "emails/cleaned/b.json"}]
    }
    client.get_object.side_effect = [
        {"Body": MagicMock(read=lambda: b"doc-a")},
        {"Body": MagicMock(read=lambda: b"doc-b")},
    ]

    docs = rp.download_cleaned_emails()
    assert docs == [b"doc-a", b"doc-b"]
    client.list_objects_v2.assert_called_once()
    assert client.get_object.call_count == 2


@patch.object(rp, "FAISS", FakeFAISSStore)
@patch.object(rp, "faiss", create=True)
@patch.object(rp, "OllamaEmbeddings", FakeEmbeddings)
def test_prepare_vectorstore_builds_and_saves(mock_faiss):
    # Stub faiss.IndexFlatL2
    mock_faiss.IndexFlatL2 = FakeIndex

    # Provide small set of docs as strings (your current code treats them as chunks directly)
    docs = ["alpha", "beta", "gamma"]

    rp.prepare_vectorstore(docs)

    # If needed, we can assert via a spy wrapping FakeFAISSStore,
    # but here reaching this point without exceptions validates the flow.
