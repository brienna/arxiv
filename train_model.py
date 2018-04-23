import gensim, os, numpy, mpld3, pandas as pd, matplotlib.pyplot as plt
from sklearn.manifold import TSNE

def main():
    with open('corpus.txt', 'r') as f:
        # do some pre-processing and return list of words for each title
        for i, line in enumerate(f):
            yield gensim.utils.simple_preprocess(line)
            # https://stackoverflow.com/questions/231767/what-does-the-yield-keyword-do

def visualize_closest_words(model, word):
    """Visualizes closest words to given word."""
    arr = numpy.empty((0, len(model[word])), dtype='f') #parameter?
    word_labels = [word]

    # Get close words
    #close_words = model.similar_by_word(word)
    close_words = model.most_similar(positive=word)

    # Save to array the vector for each close word 
    arr = numpy.append(arr, numpy.array([model[word]]), axis=0)
    for word_score in close_words:
        word_vector = model[word_score[0]]
        word_labels.append(word_score[0])
        
        arr = numpy.append(arr, numpy.array([word_vector]), axis=0)

    # Generate t-sne coordinates for 2 dimensions
    tsne = TSNE(n_components=2, random_state=0)
    numpy.set_printoptions(suppress=True)
    Y = tsne.fit_transform(arr)
    print(Y)

    x_coords = Y[:,0]
    y_coords = Y[:,1]

    # Display scatter plot
    plt.scatter(x_coords, y_coords)
    for label, x, y in zip(word_labels, x_coords, y_coords):
        plt.annotate(label, xy=(x, y), xytext=(0, 0), textcoords='offset points')
    plt.xlim(x_coords.min()+0.00005, x_coords.max()+0.00005)
    plt.ylim(y_coords.min()+0.00005, y_coords.max()+0.00005)
    plt.show()

def visualize_model(model):
    # https://stackoverflow.com/questions/43776572/visualise-word2vec-generated-from-gensim?noredirect=1&lq=1
    vocab = model.wv.vocab
    X = model[vocab]

    print('Number of unique words: ' + str(len(X)))
    print('High-dimensional vector space:')
    print(X)

    tsne = TSNE(n_components=2)
    X_tsne = tsne.fit_transform(X)
    print('2D vector space:')
    print(X_tsne)
    
    df = pd.DataFrame(X_tsne, index=vocab, columns=['x', 'y'])

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.scatter(df['x'], df['y'])

    for word, pos in df.iterrows():
        ax.annotate(word, pos)

    plt.show()
    #mpld3.show()

def detect_phrases():
    # https://radimrehurek.com/gensim/models/phrases.html
    modelfile = 'phrases_model.bin'
    if os.path.exists(modelfile):
        print('loading saved model')
        model = gensim.models.Word2Vec.load(modelfile)
        #print(model.wv.vocab)
        visualize_model(model) # TAKES FOREVER
    else:
        print('building model...')
        with open('corpus.txt', 'r') as abstracts:
            sentence_stream = [a.split(" ") for a in abstracts]
            # print(sentence_stream)
            ngrams = get_ngrams(sentence_stream)
            #sent = ['milky', 'way', 'galaxy', 'is', 'large'] # need to add u prefix to each word?
            #print(bigrams[sent])
            model = gensim.models.Word2Vec(ngrams, window=10, min_count=5, size=100)
            model.train(ngrams, total_examples=len(ngrams), epochs=10)
            model.wv.save_word2vec_format(modelfile, binary=True)
            visualize_model(model) # TAKES FOREVER

def get_ngrams(sentences):
    """
    Detects n-grams with n up to 4, and replaces those in the titles.
    https://github.com/everthemore/physics2vec/blob/master/helper.py
    """

    # Train a 2-word (bigram) phrase-detector
    bigrams = gensim.models.phrases.Phrases(sentences)

    # And construct a phraser from that (an object that will take a sentence)
    # and replace it in the bigrams that it knows by single objects)
    bigram = gensim.models.phrases.Phraser(bigrams)

    # Repeat that for trigrams; the input now are the bigrammed-titles
    trigrams = gensim.models.phrases.Phrases(bigram[sentences])
    test = ["dust", "formation", "happens", "in", "space", "and", "rapidly", "rotating", "radio", "sources", "exist"]
    print('testing: ')
    print(trigrams[test])
    trigram = gensim.models.phrases.Phraser(trigrams)

    # Analyze
    # The phrases.export_phrases(x) function returns pairs of phrases and their
    # certainty scores from x.
    bigram_info = {}
    for b, score in bigrams.export_phrases(sentences):
        bigram_info[b] = [score, bigram_info.get(b, [0, 0])[1] + 1]

    trigram_info = {}
    for b, score in trigrams.export_phrases(bigram[sentences]):
        trigram_info[b] = [score, trigram_info.get(b, [0, 0])[1] + 1]

    # Return a list of n-grammed titles
    return [trigram[t] for t in sentences]

def train_word_model():
    documents = main()
    documents = list(documents)

    modelfile = 'model.bin'
    if os.path.exists(modelfile):
        model = gensim.models.KeyedVectors.load_word2vec_format(modelfile, binary=True) 

        # visualize closest words
        #visualize_closest_words(model, 'sound')
        visualize_model(model)

    else:
        # build vocabulary and train model
        model = gensim.models.Word2Vec(
            documents,
            size=300, # Size of encoding vectors
            window=5, # Size of window scanning over text. A typical window size might be 5, meaning 5 words behind and 5 words ahead (10 in total).
            min_count=5, # Minimum number of times a word has to appear to participate
            workers=10) # have downloaded cython, is it working?
        model.train(documents, total_examples=len(documents), epochs=10)

        model.wv.save_word2vec_format(modelfile, binary=True)

        # See high dimensional 
        print(model)
        # Get raw vector for a word
        print('Vector for "star": ')
        print(model['star'])

        #visualize_model(model)

        visualize_closest_words(model, 'planet')


    #print(model.wv.most_similar(positive='variable'))

    # Get the words closest to a word
    #print(model.similar_by_word('variable'))

    #print(model.most_similar('variable'))

    #visualize_closest_words(model, 'variable')
    #detect_phrases()
    #visualize_model(model)

if __name__ == '__main__':
    """Runs if script called on command line"""
    detect_phrases()
    #train_word_model()








