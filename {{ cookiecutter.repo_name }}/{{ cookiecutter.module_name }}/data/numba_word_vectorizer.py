## Based on https://github.com/jc-healy/EmbedAllTheThings/commit/da9fd638af573e3cfdd41d7f7fdd3dfe02f1e7cd#diff-a1268b7d09e1e7b148cb6028dda26bff

from collections import defaultdict
import numpy as np
import numba
import scipy.sparse


# Just steal CountVectorizer for now; fix later
from sklearn.feature_extraction.text import CountVectorizer

_CV_INSTANCE = CountVectorizer()

_tokenizer = _CV_INSTANCE.build_tokenizer()
_preprocessor = _CV_INSTANCE.build_preprocessor()

# End stealing CountVectorizer

# Use nltk for senticizing for now
import nltk
nltk.download('punkt')

def nltk_sentencizer(text):
    return nltk.sent_tokenize(text)

# End nltk stealing


def regex_tokenizer(text):
    return _tokenizer(text)


def base_preprocessor(text):
    return _preprocessor(text)


def construct_vocabulary_and_frequency(
    raw_documents, tokenizer, preprocessor, vocabulary=None
):

    token_list = tokenizer(" ".join([preprocessor(doc) for doc in raw_documents]))
    n_tokens = len(token_list)
    if vocabulary is None:
        unique_tokens = sorted(list(set(token_list)))
        vocabulary = dict(zip(unique_tokens, range(len(unique_tokens))))

    index_list = [vocabulary[token] for token in token_list if token in vocabulary]
    token_counts = np.bincount(index_list).astype(np.float32)

    token_frequency = token_counts / n_tokens

    return vocabulary, token_frequency, n_tokens


def prune_vocabulary(
    vocabulary, token_frequencies, stop_words=None, min_df=0.0, max_df=1.0
):

    if stop_words is not None:
        tokens_to_prune = set(stop_words)
    else:
        tokens_to_prune = set([])

    reverse_vocabulary = {index: word for word, index in vocabulary.items()}

    infrequent_tokens = np.where(token_frequencies <= min_df)[0]
    frequent_tokens = np.where(token_frequencies >= max_df)[0]

    tokens_to_prune.update({reverse_vocabulary[i] for i in infrequent_tokens})
    tokens_to_prune.update({reverse_vocabulary[i] for i in frequent_tokens})

    vocab_tokens = [token for token in vocabulary if token not in tokens_to_prune]
    new_vocabulary = dict(zip(vocab_tokens, range(len(vocab_tokens))))
    new_token_frequency = np.array(
        [token_frequencies[vocabulary[token]] for token in new_vocabulary]
    )

    return new_vocabulary, new_token_frequency


def preprocess_corpus(
    raw_documents,
    sentencizer,
    tokenizer,
    preprocessor,
    vocabulary=None,
    min_df=None,
    max_df=None,
):

    # Get vocabulary and word frequecies
    vocabulary, token_frequencies, total_tokens = construct_vocabulary_and_frequency(
        raw_documents, tokenizer, preprocessor, vocabulary
    )

    if min_df is None:
        min_df = 0.0
    else:
        min_df = min_df / total_tokens

    if max_df is None:
        max_df = 1.0

    vocabulary, token_frequencies = prune_vocabulary(
        vocabulary, token_frequencies, min_df=min_df, max_df=max_df
    )

    # Convert to list of lists of sentences by sentencizing
    if sentencizer == "spacy":
        sentences = [
            list(doc.sents)
            for doc in spacy_nlp.pipe(
                raw_documents, disable=["tagger", "tokenizer", "ner", "textcat"]
            )
        ]
    else:
        sentences = [sentencizer(doc) for doc in raw_documents]

    # Pre-process and tokenize sentences
    preprocessed_sentences = [
        preprocessor(sentence) for doc in sentences for sentence in doc
    ]
    result_sequences = [
        np.array(
            [vocabulary[token] for token in tokenizer(sentence) if token in vocabulary]
        )
        for sentence in preprocessed_sentences
    ]

    return result_sequences, vocabulary, token_frequencies


@numba.njit(nogil=True)
def information_window(token_sequence, token_frequency, desired_entropy):

    result = []

    for i in range(len(token_sequence)):
        counter = 0
        current_entropy = 0.0

        for j in range(i + 1, len(token_sequence)):
            current_entropy -= np.log(token_frequency[int(token_sequence[j])])
            counter += 1
            if current_entropy >= desired_entropy:
                break

        result.append(token_sequence[i + 1 : i + 1 + counter])

    return result


@numba.njit(nogil=True)
def fixed_window(token_sequence, window_size):

    result = []

    for i in range(len(token_sequence)):
        result.append(token_sequence[i + 1 : i + window_size + 1])

    return result


@numba.njit(nogil=True)
def flat_kernel(window):
    return np.ones(len(window), dtype=np.float32)


@numba.njit(nogil=True)
def triangle_kernel(window, window_size):
    start = max(window_size, len(window))
    stop = window_size - len(window)
    return np.arange(start, stop, -1).astype(np.float32)


@numba.njit(nogil=True)
def harmonic_kernel(window):
    result = np.arange(1, len(window) + 1).astype(np.float32)
    return 1.0 / result


@numba.njit(nogil=True)
def build_skip_grams(
    token_sequence, window_function, kernel_function, window_args, kernel_args
):

    original_tokens = token_sequence
    n_original_tokens = len(original_tokens)

    if n_original_tokens < 2:
        return np.zeros((1, 3), dtype=np.float32)

    windows = window_function(token_sequence, *window_args)

    new_tokens = np.empty(
        (np.sum(np.array([len(w) for w in windows])), 3), dtype=np.float32
    )
    new_token_count = 0

    for i in range(n_original_tokens):
        head_token = original_tokens[i]
        window = windows[i]
        weights = kernel_function(window, *kernel_args)

        for j in range(len(window)):
            new_tokens[new_token_count, 0] = numba.types.float32(head_token)
            new_tokens[new_token_count, 1] = numba.types.float32(window[j])
            new_tokens[new_token_count, 2] = weights[j]
            new_token_count += 1

    return new_tokens


def document_skip_grams(
    doc, window_function, kernel_function, window_args, kernel_args
):
    skip_grams_per_sentence = [
        build_skip_grams(
            token_sequence, window_function, kernel_function, window_args, kernel_args
        )
        for token_sequence in doc
    ]
    return np.vstack(skip_grams_per_sentence)


@numba.njit(parallel=True)
def numba_remove_expectation(rows, cols, data, row_sum, col_freq):
    for i in numba.prange(data.shape[0]):
        data[i] = max(0, data[i] - row_sum[rows[i]] * col_freq[cols[i]])
    return data



def remove_expectation(count_matrix):
    result = count_matrix.tocoo().astype(np.float32)
    row_sum = np.array(result.sum(axis = 1).T)[0]
    col_sum = np.array(result.sum(axis = 0))[0]
    col_freq = col_sum/np.sum(col_sum)
    result.data = numba_remove_expectation(result.row, result.col, result.data, row_sum, col_freq)
    result.eliminate_zeros()
    return result.tocsr()


def word_word_cooccurence_matrix(
    corpus,
    window_function=fixed_window,
    kernel_function=flat_kernel,
    window_args=(5,),
    kernel_args=(),
    sentencizer=nltk_sentencizer,
    tokenizer=regex_tokenizer,
    preprocessor=base_preprocessor,
    vocabulary=None,
    stop_words=None,
    min_df=5,
    max_df=1.0,
    symmetrize=False,
):

    token_sequences, vocabulary, token_frequencies = preprocess_corpus(
        corpus, sentencizer, tokenizer, preprocessor, vocabulary, min_df, max_df
    )
    raw_coo_data = document_skip_grams(
        token_sequences, window_function, kernel_function, window_args, kernel_args
    )
    word_word_matrix = scipy.sparse.coo_matrix(
        (
            raw_coo_data.T[2],
            (raw_coo_data.T[0].astype(np.int64), raw_coo_data.T[1].astype(np.int64)),
        ),
        dtype=np.float32,
    )
    if symmetrize:
        word_word_matrix = word_word_matrix + word_word_matrix.transpose()

    token_to_index = vocabulary
    index_to_token = {index: token for token, index in vocabulary.items()}

    #word_word_matrix = remove_expectation(word_word_matrix)

    return word_word_matrix.tocsr(), token_to_index, index_to_token


def directional_word_matrix(
    corpus,
    window_function=fixed_window,
    kernel_function=flat_kernel,
    window_args=(5,),
    kernel_args=(),
    sentencizer=nltk_sentencizer,
    tokenizer=regex_tokenizer,
    preprocessor=base_preprocessor,
    vocabulary=None,
    stop_words=None,
    min_df=5,
    max_df=1.0,
):

    word_word_matrix, token_to_index, index_to_token = word_word_cooccurence_matrix(
        corpus,
        window_function,
        kernel_function,
        window_args,
        kernel_args,
        sentencizer,
        tokenizer,
        preprocessor,
        vocabulary,
        stop_words,
        min_df,
        max_df,
        symmetrize=False,
    )

    directional_word_matrix = scipy.sparse.hstack([word_word_matrix, word_word_matrix.T])

    return directional_word_matrix.tocsr(), token_to_index, index_to_token


def joint_doc_word_matrix(
    corpus,
    window_function=fixed_window,
    kernel_function=flat_kernel,
    window_args=(5,),
    kernel_args=(),
    sentencizer=nltk_sentencizer,
    tokenizer=regex_tokenizer,
    preprocessor=base_preprocessor,
    vocabulary=None,
    stop_words=None,
    min_df=5,
    max_df=1.0,
):
    
    word_matrix, token_to_index, index_to_token = directional_word_matrix(
        corpus,
        window_function,
        kernel_function,
        window_args,
        kernel_args,
        sentencizer,
        tokenizer,
        preprocessor,
        vocabulary,
        stop_words,
        min_df,
        max_df,
    )

    raw_doc_matrix = CountVectorizer(vocabulary=token_to_index).fit_transform(corpus)
    doc_matrix = scipy.sparse.hstack([raw_doc_matrix, raw_doc_matrix])
    doc_matrix = remove_expectation(doc_matrix)
    
    joint_matrix = scipy.sparse.vstack([word_matrix, doc_matrix])

    row_labels = list(token_to_index.keys()) + corpus

    return joint_matrix, token_to_index, row_labels
