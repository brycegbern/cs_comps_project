from AbstractAgent import AbstractAgent
import random
import numpy as np
import random as rd
from collections import defaultdict

class LinUCBAgent(AbstractAgent):
    '''
    Implementation of LinUCB algorithm
    '''

    class MatrixBias:
        '''
        Maintains a matrix and bias for each user in the algorithm
        Both the matrix and bias represent information learned by chosen contexts and rewards
        '''
        def __init__(self, num_features):
            self.M = np.identity(num_features)
            self.b = np.zeros(num_features)

        def update(self, payoff, context):
            self.M += np.dot(context[1], np.transpose(context[1]))
            self.b += np.dot(context[1], payoff)

    def __init__(self, num_features, alpha = 2.0):
        # maintains user matrix and bias
        self.d = num_features
        self.user_information = defaultdict(lambda: self.MatrixBias(num_features))
        self.alpha = alpha

    def choose(self, user_id, contexts, t):
        matrix_and_bias = self.user_information[user_id]
        M = matrix_and_bias.M
        b = matrix_and_bias.b

        # if user_id == 0:
        #     print(M, b)

        # Construct matrix A inverse times b
        Minv = np.linalg.inv(M)
        w = np.dot(Minv, b)

        # we need to obtain a UCB values for every action
        best_a = -1
        ucb = -np.inf
        for a in range(0, len(contexts)):
            # Calculate UCB
            cur_con = contexts[a][1]
            cur_con_T = np.transpose(cur_con)
            cur_ucb = np.dot(np.transpose(w), cur_con) + \
                      self.alpha * np.sqrt(np.transpose(np.dot(np.dot(cur_con_T, Minv), cur_con) * np.log(t + 1)))
            # retain best action, ties broken randomly
            #print(ucb, cur_ucb)
            if cur_ucb > ucb:
                best_a, ucb = a, cur_ucb
            elif cur_ucb == ucb:
                best_a = rd.choice([a, best_a])

        return best_a, contexts[best_a]

    def update(self, payoff, context, user_id):
        # Update A and b vectors
        matrix_and_bias = self.user_information[user_id]
        matrix_and_bias.update(payoff, context)
