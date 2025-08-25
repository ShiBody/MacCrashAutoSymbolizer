# WordFrequency Module
import string
from collections import Counter
import matplotlib.pyplot as plt
from pygments import lex
from pygments.token import Token
from pygments.lexers import SwiftLexer

class WordFrequency:
    def __init__(self, text):
        self.text = text

    @staticmethod
    def get_frequency_words(text, top: int = 10):
        # tokenizing each word
        tokens = list(lex(text.lower(), SwiftLexer()))
        words = [token[1] for token in tokens if token[0] == Token.Name]

        # Removing stopwords like "the", "is" .etc
        stop_words = set(['none'])
        filtered_words = [word for word in words if word not in stop_words and len(word) > 1]

        # Count word frequencies
        word_freq = Counter(filtered_words)
        app_terminate = word_freq.keys().__contains__('applicationwillterminate')
        pthread_kill = word_freq.keys().__contains__('pthread_kill') or word_freq.keys().__contains__('__pthread_kill')

        # Display top N most frequent words
        top_words = word_freq.most_common(top)
        return top_words, app_terminate, pthread_kill

    @staticmethod
    def remove_punctuation(
            words: list[str]
    ) -> list[str]:
        table = str.maketrans('', '', string.punctuation)
        return [word.translate(table) for word in words]


    # def get_frequency(self):
    #     # tokenizing each word
    #     tokens = word_tokenize(self._text.lower())
    #
    #     # Remove punctuation and stopwords
    #     table = str.maketrans('', '', string.punctuation)
    #     words = [word.translate(table) for word in tokens if word.isalpha()]
    #
    #     # Removing stopwords like "the", "is" .etc
    #     stop_words = set(stopwords.words('english'))
    #     filtered_words = [word for word in words if word not in stop_words]
    #
    #     # Count word frequencies
    #     word_freq = Counter(filtered_words)
    #
    #     # Display top N most frequent words
    #     top_words = word_freq.most_common(10)
    #     top_words = dict(top_words)
    #     return top_words

    def create_chart(self, top_words):
        if not top_words:
            raise ValueError("Usage: obj.create_chart(top_words)")
        plt.bar(top_words.keys(), top_words.values())
        plt.title('Top 10 Word Frequencies')
        plt.xlabel('Words')
        plt.ylabel('Frequency')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("static/barchart.png")

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        if not text:
            raise ValueError("Enter text to analyze word frequency")
        self._text = text
