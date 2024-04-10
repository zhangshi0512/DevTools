import spacy

class LangChainUtilities:
    def __init__(self):
        # Load a pre-trained NLP model from spacy
        self.nlp = spacy.load("en_core_web_sm")

    def tokenize(self, text):
        # Tokenize the text and return a list of token strings
        return [token.text for token in self.nlp(text)]

    def extract_entities(self, text):
        # Use the NLP model to find named entities in the text
        doc = self.nlp(text)
        return [(entity.text, entity.label_) for entity in doc.ents]

    def lemmatize(self, text):
        # Lemmatize the text and return a list of lemma strings
        return [token.lemma_ for token in self.nlp(text)]

# Example usage
if __name__ == "__main__":
    lc_utils = LangChainUtilities()
    sample_text = "Apple is looking at buying U.K. startup for $1 billion"
    print("Tokens:", lc_utils.tokenize(sample_text))
    print("Entities:", lc_utils.extract_entities(sample_text))
    print("Lemmas:", lc_utils.lemmatize(sample_text))
