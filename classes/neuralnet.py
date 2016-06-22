import numpy as np
import time
import os


class NeuralNet(object):

    """Multi-layer perceptron

        n_output: int
            number of classes
            10 for mnist data (10 digits duh)
        n_features: int
            number of features
            784 for mnist because mnist images are 28x28
        n_hidden: int
            number of hidden units
        alpha: float
            learning rate, amount to adjust by
        costs: list
            sum of sqared errors after each epoch
    """

    def __init__(self, n_output=1, n_features=198, n_hidden=50, alpha=0.2,
                 _lambda=0.9):
        self.n_output = n_output
        self.n_features = n_features
        self.n_hidden = n_hidden
        """ think of input weights as the edges that connect inputs to nodes
            in the hidden layer
        """
        self.w2 = np.random.uniform(-1.0, 1.0,
                                    size=self.n_output*(self.n_hidden+1))
        self.w2 = self.w2.reshape(self.n_output,
                                  self.n_hidden+1)
        """ think of output weights as the edges that connect hidden layer nodes
            to class outputs
        """
        self.w1 = np.random.uniform(-1.0, 1.0,
                                    size=self.n_hidden*(self.n_features+1))
        self.w1 = self.w1.reshape(self.n_hidden,
                                  self.n_features+1)

        self._et1 = np.zeros((self.w1.shape))
        self._et2 = np.zeros((self.w2.shape))

        self.alpha = alpha
        self._lambda = _lambda

    def backprop(self, a3_old, a3, X_new):
        self.w2 = self.w2 + self.alpha * (a3 - a3_old) * self._et2
        self.w1 = self.w1 + self.alpha * (a3 - a3_old) * self._et1

        a1, z2, a2, z3, a3_new = self._feedforward(X_new)
        self._et2 = self._lambda * self._et2 + (1 - a3_new) * a3_new * a2.T
        self._et1 = self._lambda * self._et1 + (1 - a3_new) * a3_new * (
            ((1 - a2[:-1, :]) * a2[:-1, :] * self.w2[:, :-1].T).dot(
                self._add_bias_unit(X_new, how='col'))
        )

    def evaluate(self, X):
        a1, z2, a2, z3, a3 = self._feedforward(X)
        if a3.shape[0] == 1:
            a3 = a3[0]
        return a3

    def _feedforward(self, X):
        a1 = self._add_bias_unit(X)
        z2 = self.w1.dot(a1.T)
        a2 = self._sigmoid(z2)
        a2 = self._add_bias_unit(a2, how='row')
        z3 = self.w2.dot(a2)
        a3 = self._sigmoid(z3)
        return a1, z2, a2, z3, a3

    def save(self, folder):
        path = os.getcwd() + "/" + folder
        if os.path.exists(folder):
            folder = folder + time.strftime("%c").replace(" ", "_")
        os.makedirs(path)
        np.savetxt(path + "/w1.txt", self.w1)
        np.savetxt(path + "/w2.txt", self.w2)
        np.savetxt(path + "/et1.txt", self._et1)
        np.savetxt(path + "/et2.txt", self._et2)

    def load(self, fname):
        if fname[-1] != "/":
            fname.append("/")
        self.w1 = np.loadtxt(fname + "w1.txt")
        self.w2 = np.loadtxt(fname + "w2.txt")
        self._et1 = np.loadtxt(fname + "et1.txt")
        self._et2 = np.loadtxt(fname + "et2.txt")

    def __setattr__(self, name, value):
        if name in ["w1", "w2", "_et1", "_et2"]:
            if len(value.shape) == 1:
                value = value.reshape(1, value.shape[0])
        super(NeuralNet, self).__setattr__(name, value)

    def _sigmoid(self, z):
        return 1.0/(1.0 + np.exp(-z))

    def _sigmoid_gradient(self, z):
        sg = self._sigmoid(z)
        return sg * (1-sg)

    def _add_bias_unit(self, X, how='col'):
        if (isinstance(X, list)):
            X = np.asarray(X)
        if len(X.shape) == 1:
            X = X.reshape(1, X.shape[0])
        if how == 'col':
            X_new = np.ones((X.shape[0], X.shape[1]+1))
            X_new[:, :-1] = X
        elif how == 'row':
            X_new = np.ones((X.shape[0]+1, X.shape[1]))
            X_new[:-1, :] = X
        else:
            raise AttributeError('`how` must be `col` or `row`')
        return X_new
