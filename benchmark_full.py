import time
import streamlit as st
import os

# Mock streamlit session state to avoid errors when importing qa_app
class MockSessionState(dict):
    def __getattr__(self, key):
        return self.get(key)
    def __setattr__(self, key, value):
        self[key] = value

st.session_state = MockSessionState()

try:
    from qa_app import get_embeddings
except ImportError as e:
    print(f"Error importing qa_app: {e}")
    import sys
    sys.exit(1)

import warnings
warnings.filterwarnings('ignore')

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
