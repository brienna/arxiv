import os
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
import string, gensim
from gensim import corpora

stop = set(stopwords.words('english'))
exclude = set(string.punctuation)
lemma = WordNetLemmatizer()

def clean(doc):
    stop_free = " ".join([i for i in doc.lower().split() if i not in stop])
    print('created stop_free')
    punc_free = ''.join(ch for ch in stop_free if ch not in exclude)
    print('created punc_free')
    normalized = " ".join(lemma.lemmatize(word) for word in punc_free.split())
    print('created normalized')
    return normalized


def concat_files():
    data = []

    folder = 'txt'
    for filename in os.listdir('txt'):
        if filename.endswith('.txt'):
            with open('txt/' + filename, 'r') as open_file:
                data.append(open_file.read().replace('\n', ''))
    return data


if __name__ == '__main__':
    """Runs if script called on command line"""
    
    # Build array from all documents
    data = concat_files()
    # Clean and preprocess
    data_clean = [clean(doc).split() for doc in data]  

    # Create the term dictionary of our corpus, where every unique term is assigned an inde
    dictionary = corpora.Dictionary(data_clean)

    # Converting list of documents (corpus) into Document Term Matrix using dictionary prepared above.
    doc_term_matrix = [dictionary.doc2bow(doc) for doc in data_clean]

    # Creating the object for LDA model using gensim library
    Lda = gensim.models.ldamodel.LdaModel

    # Running and Trainign LDA model on the document term matrix.
    ldamodel = Lda(doc_term_matrix, num_topics=3, id2word=dictionary, passes=50)
    print(ldamodel.print_topics(num_topics=3, num_words=3))

