import sys
import unittest
from unittest.mock import MagicMock, patch
from io import StringIO

# Setup mocks before importing qa_app
mock_st = MagicMock()
# Handle decorators
def identity(f): return f
mock_st.cache_data = identity
mock_st.cache_resource = identity

sys.modules["streamlit"] = mock_st
sys.modules["PyPDF2"] = MagicMock()
sys.modules["dotenv"] = MagicMock()
sys.modules["langchain"] = MagicMock()
sys.modules["langchain.vectorstores"] = MagicMock()
sys.modules["langchain.chains"] = MagicMock()
sys.modules["langchain.chat_models"] = MagicMock()
sys.modules["langchain.retrievers"] = MagicMock()
sys.modules["langchain.callbacks"] = MagicMock()
sys.modules["langchain.embeddings.openai"] = MagicMock()
sys.modules["langchain.text_splitter"] = MagicMock()
sys.modules["langchain.callbacks.streaming_stdout"] = MagicMock()
sys.modules["langchain.callbacks.base"] = MagicMock()
sys.modules["langchain.embeddings"] = MagicMock()

import qa_app

class TestQAApp(unittest.TestCase):

    def setUp(self):
        # Reset mocks before each test
        mock_st.reset_mock()

    @patch('PyPDF2.PdfReader')
    def test_load_docs_pdf(self, mock_pdf_reader):
        # Setup mock for PDF file
        mock_file = MagicMock()
        mock_file.name = "test.pdf"

        # Setup PDF reader mock
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF content"
        mock_pdf_reader.return_value.pages = [mock_page]

        result = qa_app.load_docs([mock_file])

        self.assertEqual(result, "PDF content")
        mock_pdf_reader.assert_called_once_with(mock_file)
        mock_page.extract_text.assert_called_once()
        mock_st.info.assert_called()
        mock_st.progress.assert_called()

    def test_load_docs_txt(self):
        # Setup mock for TXT file
        mock_file = MagicMock()
        mock_file.name = "test.txt"
        mock_file.getvalue.return_value = b"TXT content"

        result = qa_app.load_docs([mock_file])

        self.assertEqual(result, "TXT content")
        mock_file.getvalue.assert_called_once()
        mock_st.info.assert_called()
        mock_st.progress.assert_called()

    def test_load_docs_unsupported(self):
        mock_file = MagicMock()
        mock_file.name = "test.jpg"

        result = qa_app.load_docs([mock_file])

        self.assertEqual(result, "")
        mock_st.warning.assert_called_once_with('Please provide txt or pdf.', icon="⚠️")

    @patch('qa_app.RecursiveCharacterTextSplitter')
    def test_split_texts(self, mock_splitter_class):
        mock_splitter = mock_splitter_class.return_value
        mock_splitter.split_text.return_value = ["chunk1", "chunk2"]

        result = qa_app.split_texts("some text", 1000, 0, "any")

        self.assertEqual(result, ["chunk1", "chunk2"])
        mock_splitter_class.assert_called_once_with(chunk_size=1000, chunk_overlap=0)
        mock_splitter.split_text.assert_called_once_with("some text")

    @patch('qa_app.RecursiveCharacterTextSplitter')
    def test_split_texts_empty(self, mock_splitter_class):
        mock_splitter = mock_splitter_class.return_value
        mock_splitter.split_text.return_value = []

        # In this mock environment, st.stop() might not raise SystemExit unless we tell it to
        mock_st.stop.side_effect = SystemExit

        with self.assertRaises(SystemExit):
            qa_app.split_texts("some text", 1000, 0, "any")

        mock_st.error.assert_called_once_with("Failed to split document")
        mock_st.stop.assert_called_once()

    @patch('qa_app.FAISS')
    def test_create_retriever_similarity(self, mock_faiss):
        mock_embeddings = MagicMock()
        mock_splits = ["chunk1"]
        mock_vectorstore = mock_faiss.from_texts.return_value
        mock_retriever = mock_vectorstore.as_retriever.return_value

        result = qa_app.create_retriever(mock_embeddings, mock_splits, "SIMILARITY SEARCH")

        self.assertEqual(result, mock_retriever)
        mock_faiss.from_texts.assert_called_once_with(mock_splits, mock_embeddings)
        mock_vectorstore.as_retriever.assert_called_once_with(k=5)

    @patch('qa_app.FAISS')
    def test_create_retriever_similarity_error(self, mock_faiss):
        mock_faiss.from_texts.side_effect = ValueError("Test Error")

        result = qa_app.create_retriever(MagicMock(), ["chunk"], "SIMILARITY SEARCH")

        self.assertIsNone(result)
        mock_st.error.assert_called_once_with("Error creating vectorstore: Test Error")

    @patch('qa_app.SVMRetriever')
    def test_create_retriever_svm(self, mock_svm):
        mock_embeddings = MagicMock()
        mock_splits = ["chunk1"]
        mock_retriever = mock_svm.from_texts.return_value

        result = qa_app.create_retriever(mock_embeddings, mock_splits, "SUPPORT VECTOR MACHINES")

        self.assertEqual(result, mock_retriever)
        mock_svm.from_texts.assert_called_once_with(mock_splits, mock_embeddings)

    @patch('qa_app.ChatOpenAI')
    @patch('qa_app.QAGenerationChain')
    @patch('random.randint')
    def test_generate_eval(self, mock_randint, mock_qa_chain_class, mock_chat_openai):
        mock_randint.return_value = 0
        mock_chain = mock_qa_chain_class.from_llm.return_value
        mock_chain.run.return_value = [{"question": "q", "answer": "a"}]

        text = "This is a long text for testing evaluation generation."
        result = qa_app.generate_eval(text, 2, 10)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], {"question": "q", "answer": "a"})
        self.assertEqual(mock_chain.run.call_count, 2)
        mock_st.info.assert_called()
        mock_st.progress.assert_called()

    @patch('qa_app.ChatOpenAI')
    @patch('qa_app.QAGenerationChain')
    @patch('random.randint')
    def test_generate_eval_error(self, mock_randint, mock_qa_chain_class, mock_chat_openai):
        mock_randint.return_value = 0
        mock_chain = mock_qa_chain_class.from_llm.return_value
        mock_chain.run.side_effect = Exception("Chain Error")

        text = "Short text"
        result = qa_app.generate_eval(text, 1, 5)

        self.assertEqual(result, [])
        mock_st.warning.assert_called()

if __name__ == '__main__':
    unittest.main()
