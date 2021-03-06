from AbstractUserContextManager import AbstractUserContextManager
from DummyAgent import DummyAgent
from GOBLinAgent import GOBLinAgent
from LinUCBAgent import LinUCBAgent
from BlockAgent import BlockAgent
from MacroAgent import MacroAgent
import numpy
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.decomposition import TruncatedSVD
from collections import defaultdict
import uuid
import random


class FourCliquesContextManager(AbstractUserContextManager):
    """
    For a social network with 4 cliques, each with 25 users, assigns each user within a 
    clique a random vector of size 25 representing the "ideal" context vector for that user.
    Returns random context vectors for any user when getting users and contexts. 
    Computes payoff as user_vector dot context_vector + uniform distribution within epsilon --
    Epsilon is payoff noise.
    """
    CLIQUE_SIZE = 25
    NUM_CLIQUES = 4
    PROVIDED_CONTEXTS = 10

    def __init__(self, epsilon=0.0, num_features=25):
        self.user_vectors = []
        # user_vectors will contain NUM_CLIQUES * CLIQUE_SIZE vectors, CLIQUE_SIZE of the same vector for each clique
        self.epsilon = epsilon
        self.num_features = num_features

        for i in range(self.NUM_CLIQUES):
            rand_vector = numpy.random.uniform(low=-1, high=1, size=(num_features,))
            norm = numpy.linalg.norm(rand_vector)
            rand_vector = rand_vector / norm
            for j in range(self.CLIQUE_SIZE):
                self.user_vectors.append(rand_vector)

    def get_user_and_contexts(self):
        # since 4cliques has no "real" contexts, we generate PROVIDED_CONTEXTS context vectors on the fly
        # to be chosen from for our chosen user
        user = random.randrange(0, self.NUM_CLIQUES * self.CLIQUE_SIZE)
        context_vectors = []
        for i in range(self.PROVIDED_CONTEXTS):
            # generate random context vector of length 1
            rand_vector = numpy.random.uniform(low=-1, high=1, size=(self.num_features,))
            norm = numpy.linalg.norm(rand_vector)
            rand_vector = rand_vector / norm
            # contexts are associated with a unique identifier, in 4cliques, as each context is uniquely generated,
            # we generate a unique identifier for each context before releasing it. For other datasets, this unique
            # identifier is provided in the dataset.
            context_vectors.append((uuid.uuid1(), rand_vector))

        return user, context_vectors

    def get_payoff(self, user, context):
        user_vector = self.user_vectors[user]
        context_vector = context[1]
        # payoff is dotted user_vector and context_vector plus a random sample bounded by epsilon 
        return numpy.dot(user_vector, context_vector) + numpy.random.uniform(-self.epsilon, self.epsilon)

    @classmethod
    def generate_cliques(cls, threshold):
        graph = numpy.zeros((100, 100))
        # creates a block adjacency matrix with 4 25 x 25 blocks of ones
        # along the diagonal corresponding to each clique
        for i in range(cls.NUM_CLIQUES):
            for j in range(cls.CLIQUE_SIZE):
                for k in range(cls.CLIQUE_SIZE):
                    graph[j + i * cls.CLIQUE_SIZE][k + i * cls.CLIQUE_SIZE] = 1
        noise_generated = numpy.random.rand(cls.NUM_CLIQUES * cls.CLIQUE_SIZE, cls.NUM_CLIQUES * cls.CLIQUE_SIZE)
        # get top triangle of matrix without diagonal, and create symmetrical matrix
        noise_top = numpy.triu(noise_generated, 1)
        noise = noise_top + numpy.transpose(noise_top)

        def check_threshold(element):
            if element > threshold:
                return 1
            else:
                return 0

        # vectorizing a function makes it apply elementwise to a matrix
        vectorized_above_threshold = numpy.vectorize(check_threshold)
        above_threshold = vectorized_above_threshold(noise)
        # swap values where the noise is above the threshold
        result = numpy.logical_xor(graph, above_threshold)
        # logical xor returns trues and falses, we need ones and zeroes, which we produce with another
        # vectorized function
        convert_from_true_false_to_1_0 = numpy.vectorize(lambda x: 1 if x else 0)
        return convert_from_true_false_to_1_0(result)


class TaggedUserContextManager(AbstractUserContextManager):
    """
    For a social network with num_users users associated truly with contexts true_associations. 
    For get_user_and_contexts, returns a random collection of context vectors such that one is
    truly associated with the user. To compute payoff, returns 1 if the context is truly associated
    with the user and zero otherwise.
    """

    def __init__(self, num_users, true_associations, contexts):
        self.true_associations = true_associations
        self.contexts = contexts
        self.num_users = num_users
        self.context_dict = {}
        for context in self.contexts:
            self.context_dict[context[0]] = context

    def get_user_and_contexts(self):
        user = random.randrange(0, self.num_users)
        associated_contexts = self.true_associations[user]
        base_contexts = random.choices(self.contexts, k=24)
        truth_context_id = random.choice(associated_contexts)
        contexts = base_contexts + [self.context_dict[truth_context_id]]
        random.shuffle(contexts)
        return user, contexts

    def get_payoff(self, user, context):
        if context[0] in self.true_associations[user]:
            return 1
        else:
            return 0


def load_data(dataset_location, four_cliques_graph_noise=0, four_cliques_epsilon=0.1, num_features=25, num_clusters=None):
    """
    :param dataset_location: location of dataset folder, or 4cliques for builtin 4cliques dataset
    :param four_cliques_graph_noise: graph noise for 4cliques
    :param four_cliques_epsilon: payoff noise for 4cliques
    :param num_features: number of features in vector
    :return: ContextManager, network graph (numpy 2-dimensional matrix of ones and zeroes)
    """
    if num_clusters:
        cluster_to_idx, idx_to_cluster = load_clusters(dataset_location, num_clusters)
    else:
        cluster_to_idx, idx_to_cluster = None, None
    if dataset_location != "4cliques":
        graph, num_users = load_graph(dataset_location)
        return TaggedUserContextManager(num_users, load_true_associations(dataset_location),
                                        load_and_generate_contexts(dataset_location, num_features=num_features)), graph, cluster_to_idx, idx_to_cluster
    else:
        threshold = 1 - four_cliques_graph_noise
        graph = FourCliquesContextManager.generate_cliques(threshold)
        return FourCliquesContextManager(epsilon=four_cliques_epsilon, num_features=num_features), graph, cluster_to_idx, idx_to_cluster


def load_graph(dataset_location):
    # graph is already represented as an adjacency matrix
    f = open("{}/graph.csv".format(dataset_location), 'r')
    rows = []
    for line in f:
        rows.append([int(s) for s in line.split(',')])
    num_users = len(rows[0])
    array = numpy.zeros((num_users, num_users))
    for i in range(num_users):
        for j in range(num_users):
            array[i][j] = rows[i][j]
    return array, num_users


def load_true_associations(dataset_location):
    # true associations are pairs of users and contexts that that user has actually interacted with
    f = open("{}/user_contexts.csv".format(dataset_location), 'r')
    user_contexts = defaultdict(list)
    for line in f:
        user_str, context = line.split(',')
        user_str = user_str.strip()
        context = context.strip()
        user = int(user_str)
        user_contexts[user].append(context)
    return user_contexts


def load_and_generate_contexts(dataset_location, num_features=25):
    # produce context indices from context names
    context_idx = 0
    context_to_idx = {}
    contexts = open("{}/context_names.csv".format(dataset_location), 'r', encoding="utf-8")
    for line in contexts:
        context = line.split(',')[0]
        if context not in context_to_idx:
            context_to_idx[context] = context_idx
            context_idx += 1

    f = open("{}/context_tags.csv".format(dataset_location), 'r')
    tag_idx = 0
    tag_to_idx = {}
    context_to_tags = []
    # load associations between contexts and tags and index tags
    for line in f:
        context, tag = line.split(',')
        if tag not in tag_to_idx:
            tag_to_idx[tag] = tag_idx
            tag_idx += 1
        if context not in context_to_idx:
            context_to_idx[context] = context_idx
            context_idx += 1
        context_to_tags.append((context_to_idx[context], tag_to_idx[tag]))
    # create matrix context_num by tag_num in size whose elements are 1
    # if the context has been associated with that tag, and zero otherwise
    array = numpy.zeros((context_idx, tag_idx))

    for context_tag_pair in context_to_tags:
        context, tag = context_tag_pair
        array[context][tag] = 1
    # perform tfidf transformation
    # value in array is decreased corresponding to the number of contexts that are tagged
    # with a given tag, making it so that rare tags count for more. TFIDF also weights by
    # the number of times that the tag appears with a given context, but since here all are 1
    # this is not meaningful
    transformer = TfidfTransformer()
    contexts_array = transformer.fit_transform(array)

    # use singular value decomposition to compress our high-dimensional sparse representation of each context
    # into a num-features-dimensional dense representation.
    svd = TruncatedSVD(n_components=num_features)
    svd_contexts = svd.fit_transform(contexts_array)
    all_contexts = []

    for context_id in context_to_idx.keys():
        # extract associated vector generated from svd for each context
        vector = svd_contexts[context_to_idx[context_id]]
        all_contexts.append((context_id, vector))
        # the format for a context is a tuple of a context_id and an associated vector
    return all_contexts


def load_clusters(dataset_location, num_clusters):
    if num_clusters not in [5, 10, 20, 50, 100, 200]:
        raise Exception("Invalid cluster number!")
    filename = "{}/clustered_graph.part.{}".format(dataset_location, num_clusters)
    idx_to_cluster = {} 
    with open(filename, "r") as cluster_file:
        for i, line in enumerate(cluster_file):
            if line.strip():
                idx_to_cluster[i] = int(line.strip())
    
    cluster_to_idx = defaultdict(lambda: [])
    for idx in idx_to_cluster.keys():
        cluster = idx_to_cluster[idx]
        cluster_to_idx[cluster].append(idx)
    return cluster_to_idx, idx_to_cluster


def load_agent(algorithm_name, num_features, alpha, graph, cluster_data):
    if algorithm_name == "dummy":
        return DummyAgent()
    elif algorithm_name == "linucb":
        return LinUCBAgent(num_features, alpha)
    elif algorithm_name == "linucbsin":
        return LinUCBAgent(num_features, alpha, True)
    elif algorithm_name == "goblin":
        return GOBLinAgent(graph, len(graph), alpha=alpha, vector_size=num_features)
    elif algorithm_name == "block":
        return BlockAgent(graph, len(graph), cluster_data, alpha=alpha,  vector_size=num_features)
    elif algorithm_name == "macro":
        return MacroAgent(graph, len(graph), cluster_data, alpha=alpha, vector_size=num_features)
    else:
        raise Exception("Algorithm not implemented! Try linucb, linucbsin, goblin")

