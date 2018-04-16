import gensim, os, numpy
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

def main():
    with open('titles.txt', 'r') as f:
        # do some pre-processing and return list of words for each title
        for i, line in enumerate(f):
            yield gensim.utils.simple_preprocess(line)
            # https://stackoverflow.com/questions/231767/what-does-the-yield-keyword-do

def visualize_closest_words(model, word):
    """Visualizes closest words to given word."""
    arr = numpy.empty((0, len(model[word])), dtype='f') #parameter?
    word_labels = [word]

    # Get close words
    close_words = model.similar_by_word(word)

    # Save to array the vector for each close word 
    arr = numpy.append(arr, numpy.array([model[word]]), axis=0)
    for word_score in close_words:
        word_vector = model[word_score[0]]
        word_labels.append(word_score[0])
        print(word_score)
        arr = numpy.append(arr, numpy.array([word_vector]), axis=0)

    # Generate t-sne coordinates for 2 dimensions
    tsne = TSNE(n_components=2, random_state=0)
    numpy.set_printoptions(suppress=True)
    Y = tsne.fit_transform(arr)

    x_coords = Y[:,0]
    y_coords = Y[:,1]

    # Display scatter plot
    plt.scatter(x_coords, y_coords)
    for label, x, y in zip(word_labels, x_coords, y_coords):
        plt.annotate(label, xy=(x, y), xytext=(0, 0), textcoords='offset points')
    plt.xlim(x_coords.min()+0.00005, x_coords.max()+0.00005)
    plt.ylim(y_coords.min()+0.00005, y_coords.max()+0.00005)
    plt.show()

if __name__ == '__main__':
    """Runs if script called on command line"""
    documents = main()
    documents = list(documents)

    # build vocabulary and train model
    model = gensim.models.Word2Vec(
        documents,
        size=150,
        window=10,
        min_count=1,
        workers=10) # have downloaded cython, is it working?
    model.train(documents, total_examples=len(documents), epochs=10)

    print(model)

    w1 = "gravity"
    #print(model.wv.most_similar(positive=w1))

    # Get raw vector for a word
    #print(model['variable'])

    # Get the words closest to a word
    #print(model.similar_by_word('variable'))



    visualize_closest_words(model, 'milky')









