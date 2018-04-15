import gensim, os

def main():
    with open('titles.txt', 'r') as f:
        # do some pre-processing and return list of words for each title
        for i, line in enumerate(f):
            yield gensim.utils.simple_preprocess(line)
            # https://stackoverflow.com/questions/231767/what-does-the-yield-keyword-do

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

    w1 = "gravity"
    print(model.wv.most_similar(positive=w1))
