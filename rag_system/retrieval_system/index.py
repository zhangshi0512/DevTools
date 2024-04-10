from collections import defaultdict
import nltk
from nltk.tokenize import word_tokenize

if not nltk.data.find('tokenizers/punkt'):
    nltk.download('punkt', quiet=True)


class DocumentIndexer:
    def __init__(self):
        self.inverted_index = defaultdict(list)
        self.documents = {}

    def add_document(self, doc_id, text):
        self.documents[doc_id] = text
        tokens = word_tokenize(text.lower())
        for token in tokens:
            if doc_id not in self.inverted_index[token]:
                self.inverted_index[token].append(doc_id)

    def get_document(self, doc_id):
        return self.documents.get(doc_id, "")
