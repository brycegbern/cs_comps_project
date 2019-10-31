from AbstractUserContextManager import AbstractUserContextManager
import numpy
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.decomposition import TruncatedSVD 
from collections import defaultdict
import random

class FourCliquesContextManager(AbstractUserContextManager):
    def __init__(self, epsilon):
        self.user_vectors = []
        self.epsilon = epsilon
        for i in range(4):
            rand_vector = numpy.random.rand(25)
            norm = numpy.linalg.norm(rand_vector)
            rand_vector = rand_vector / norm
            for j in range(25):
                self.user_vectors.append(rand_vector)
    def get_user_and_contexts(self):
        user = random.randrange(0,100)
        context_vectors = []
        for i in range(25):
            rand_vector = numpy.random.rand(25)
            norm = numpy.linalg.norm(rand_vector)
            rand_vector = rand_vector / norm
            context_vectors.append(("fakeID",rand_vector))

        return user, context_vectors
    def get_payoff(self, user, context):
        user_vector = self.user_vectors[user]
        context_vector = context[1]
        return numpy.dot(user_vector, context_vector) + numpy.random.uniform(-self.epsilon, self.epsilon)
    
 
        

        
        


class TaggedUserContextManager(AbstractUserContextManager):
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
        return user, contexts 
    def get_payoff(self, user, context):
        if context[0] in self.true_associations[user]:
            return 1
        else:
            return 0

         


def load_data(dataset_location):
    if dataset_location != "4CLIQUES":
        graph, num_users = load_graph(dataset_location)
        return TaggedUserContextManager(num_users, load_true_associations(dataset_location), load_and_generate_contexts(dataset_location)), graph
    else:
        graph = generate_cliques(.9)
        return FourCliquesContextManager(.1), graph


    
    

def generate_cliques(threshold):
    graph = numpy.zeros((100,100))
    for i in range(4):
        for j in range(25):
            for k in range(25):
                graph[j+i*25][k+i*25] = 1
    noise = numpy.random.rand(100,100)
    def check_threshold(element):
        if element > threshold:
            return 1
        else:
            return 0
    vfunc = numpy.vectorize(check_threshold)
    noisethreshold = vfunc(noise)
    result = numpy.logical_xor(graph, noisethreshold)
    vfunc = numpy.vectorize(lambda x: 1 if x else 0)
    return vfunc(result)





        
def load_graph(dataset_location):
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
    f = open("{}/user_contexts.csv".format(dataset_location), 'r')
    user_contexts = defaultdict(list)
    for line in f:
        user_str, context = line.split(',')
        user_str = user_str.strip()
        context = context.strip()
        user = int(user_str)
        user_contexts[user].append(context)
    return user_contexts


def load_and_generate_contexts(dataset_location):
    f = open("{}/context_tags.csv".format(dataset_location), 'r')
    context_idx = 0
    tag_idx = 0
    context_to_idx = {}
    tag_to_idx = {}
    context_to_tags = []
    for line in f:
        context, tag = line.split(',')
        if context not in context_to_idx:
            context_to_idx[context] = context_idx
            context_idx += 1
        if tag not in tag_to_idx:
            tag_to_idx[tag] = tag_idx
            tag_idx += 1
        context_to_tags.append((context_to_idx[context], tag_to_idx[tag]))
    array = numpy.zeros((context_idx, tag_idx))

    for context_tag_pair in context_to_tags:
        context, tag = context_tag_pair
        array[context][tag] += 1

    transformer = TfidfTransformer()

    contexts_array = transformer.fit_transform(array)
    
    svd = TruncatedSVD(n_components=25)
    
    svd_contexts = svd.fit_transform(contexts_array)
    all_contexts = []
    
    for context in context_to_idx.keys():
        vector = svd_contexts[context_to_idx[context]]
        all_contexts.append((context, vector)) 

    return all_contexts




if __name__ == "__main__":

    ucm, graph = load_data('4CLIQUES')
    user, contexts = ucm.get_user_and_contexts()
    for context in contexts:
        print(ucm.get_payoff(user, context))
    

