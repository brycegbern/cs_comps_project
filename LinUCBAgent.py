from AbstractAgent import AbstractAgent
import numpy as np
import random as rd
from collections import defaultdict
import math

class LinUCBAgent(AbstractAgent):
    """
    Implementation of LinUCB algorithm
    """

    class MatrixBias:
        """
        Maintains a matrix and bias for each user in the algorithm
        Both the matrix and bias represent infor
        mation learned by chosen contexts and rewards
        """

        def __init__(self, num_features):
            self.M = np.identity(num_features)
            self.b = np.zeros(num_features)

        def update(self, payoff, context):
            self.M += np.dot(context[1], np.transpose(context[1]))
            self.b += np.dot(context[1], payoff)

    def __init__(self, num_features, alpha=0.1, is_sin=False):
        # maintains user matrix and bias
        self.d = num_features
        self.user_information = defaultdict(lambda: self.MatrixBias(num_features))
        self.alpha = alpha
        self.is_sin = is_sin

    def choose(self, user_id, contexts, timestep):
        """
        Chooses best context for user, taking into account exploration, at current timestep.
        """
        # If LinUCB-SIN, then use only one matrix_and_bias instance -- i.e., every user is treated as user 0
        if self.is_sin:
            user_id = 0
        matrix_and_bias = self.user_information[user_id]
        M = matrix_and_bias.M
        b = matrix_and_bias.b

        # Construct matrix M inverse times b
        Minv = np.linalg.inv(M)
        w = np.dot(Minv, b)

        # we need to obtain a score for every context
        best_idx = -1
        score = -np.inf
        for i in range(0, len(contexts)):
            # Calculate UCB
            cur_con = contexts[i][1]
            cur_con_T = np.transpose(cur_con)

            ucb = self.alpha * np.sqrt(np.linalg.multi_dot([cur_con_T, Minv, cur_con]) * math.log(timestep + 1))
            cur_score = np.dot(np.transpose(w), cur_con) + ucb

            # retain best action, ties broken randomly
            if cur_score > score:
                best_idx, score = i, cur_score

        return contexts[best_idx]

    def update(self, payoff, context, user_id):
        """
        Updates matrices based on payoff of chosen context
        """
        # If LinUCB-SIN, we are updating only user_id 0
        if self.is_sin:
            user_id = 0
        # Update A and b vectors
        matrix_and_bias = self.user_information[user_id]
        matrix_and_bias.update(payoff, context)
