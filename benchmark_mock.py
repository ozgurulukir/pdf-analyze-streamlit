import time
import sys
import unittest.mock as mock

class DummyModule(mock.MagicMock):
    pass

st_mock = DummyModule()
def cache_mock(func):
    """Simple cache mock that just stores the result"""
    cache = {}
    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    return wrapper

st_mock.cache_resource = cache_mock
st_mock.cache_data = cache_mock
sys.modules['streamlit'] = st_mock

sys.modules['PyPDF2'] = DummyModule()
sys.modules['langchain'] = DummyModule()
sys.modules['langchain.chat_models'] = DummyModule()
sys.modules['langchain.embeddings.openai'] = DummyModule()
sys.modules['langchain.document_loaders'] = DummyModule()
sys.modules['langchain.text_splitter'] = DummyModule()
sys.modules['langchain.vectorstores'] = DummyModule()
sys.modules['langchain.retrievers'] = DummyModule()
sys.modules['langchain.chains'] = DummyModule()
sys.modules['langchain.callbacks'] = DummyModule()
sys.modules['langchain.callbacks.streaming_stdout'] = DummyModule()
sys.modules['langchain.callbacks.base'] = DummyModule()
sys.modules['langchain.embeddings'] = DummyModule()

class MockHuggingFaceEmbeddings:
    def __init__(self):
        time.sleep(1) # mock loading time

sys.modules['langchain.embeddings'].HuggingFaceEmbeddings = MockHuggingFaceEmbeddings

from qa_app import get_embeddings

print("Starting benchmark...", flush=True)

# First call (without cache, should be slow)
start_time = time.time()
embeddings1 = get_embeddings("HuggingFace Embeddings(slower)", "dummy_key")
end_time = time.time()
first_call_time = end_time - start_time
print(f"HuggingFaceEmbeddings first init time (without cache): {first_call_time:.4f} seconds", flush=True)

# Second call (with cache, should be fast)
start_time = time.time()
embeddings2 = get_embeddings("HuggingFace Embeddings(slower)", "dummy_key")
end_time = time.time()
second_call_time = end_time - start_time
print(f"HuggingFaceEmbeddings second init time (with cache): {second_call_time:.4f} seconds", flush=True)

if first_call_time > 0:
    improvement = (first_call_time - second_call_time) / first_call_time * 100
    print(f"Performance improvement: {improvement:.2f}%", flush=True)
