'This module is for 3 layers newral network.'
import numpy as np
import matplotlib.pyplot as plt
import scipy.io as spi
from scipy.optimize import *
from PIL import Image

def activation_func(z, type="sigmoid"):
    '''activation function used in neural network
    default: sigmoid function
    '''
    if type == "sigmoid":
        return 1 / (1 + np.exp(-z))
    else:
        return z

def activation_difffunc(z, type="sigmoid"):
    'differential of activation function'
    if type == "sigmoid":
        return activation_func(z) * (1 - activation_func(z))
    else:
        return 1

class NeuralNetwork(object):
    """this is a class for 3 layers NeuralNetwork"""
    def __init__(self, layer_num, filename=None):
        if filename is None:
            'initialize network'
            self.INPUT_LAYER, self.HIDDEN_LAYER, self.OUTPUT_LAYER = layer_num
            # bias
            self.INPUT_LAYER += 1
            self.HIDDEN_LAYER += 1

            self.setparams()
            self.trainAccuracies = []
            self.testAccuracies = []
        else:
            f = open(filename, 'r')

    def initW(self):
        'initialize weight'
        const = (self.HIDDEN_LAYER-1) + (self.INPUT_LAYER-1) + 1
        tempW2 = np.random.rand(self.HIDDEN_LAYER-1, self.INPUT_LAYER-1) * 2 * np.sqrt(6/const) - np.sqrt(6/const)
        self.W2 = np.concatenate((np.zeros((self.HIDDEN_LAYER-1, 1)), tempW2), axis=1)

        const = (self.HIDDEN_LAYER-1) + self.OUTPUT_LAYER + 1
        self.W3 = np.concatenate((np.zeros((self.OUTPUT_LAYER, 1)), np.random.rand(self.OUTPUT_LAYER, self.HIDDEN_LAYER-1) * 2 * np.sqrt(6/const) - np.sqrt(6/const)), axis=1)

    def updateW(self, inputdatum, outputdatum):
        'update weight'
        gradW2, gradW3 = self.backpropagation(inputdatum, outputdatum)
        # gradW2, gradW3 = self.numericalGrad(inputdatum, outputdatum)
        self.W2 -= self.mu * gradW2
        self.W3 -= self.mu * gradW3

    def setparams(self, mu=1e-4, lam=1e-6, rho=0.05, beta=1e-6, MaxTrial=50, MaxEpoch=100, TestRatio=10):
        'set parameters'
        self.mu = mu
        self.lam = lam
        self.rho = rho
        self.beta = beta
        self.MaxTrial = MaxTrial
        self.MaxEpoch = MaxEpoch
        # percentage
        self.TestRatio = TestRatio

    def train(self, inputdata, outputdata):
        'train network'
        # check in row
        if inputdata.shape[0] != outputdata.shape[0]:
            print("input data size is NOT equal to output data size")
            exit(0)

        self.initW()

        self.inData = inputdata.transpose()
        self.outData = outputdata.transpose()

        w0 = np.concatenate((self.W2.flatten(), self.W3.flatten())).copy()
        print(w0.shape)

        # self.checkgrad(w0)

        minimize(self.cost, w0, jac=self.numericalGrad, method='L-BFGS-B', options={'maxiter':self.MaxEpoch, 'disp': True})

        # for i in range(self.MaxEpoch):

    def cost(self, args):
        'cost function used in this NN'
        w2 = args[0:self.W2.size]
        w3 = args[self.W2.size:]
        w2 = w2.reshape(self.W2.shape[0], self.W2.shape[1])
        w3 = w3.reshape(self.W3.shape[0], self.W3.shape[1])
        m = self.inData.shape[1]
        J =  0.5 / m * np.sum(np.square(self.outData - self.propagation(w2, w3))) + self.lam * 0.5 * (np.sum(np.square(w2[:, 1:])) + np.sum(np.square(w3[:, 1:])))

        J += self.beta * np.sum(self.rho * np.log(self.rho/self.activeNum) + (1 - self.rho) * np.log((1-self.rho)/(1-self.activeNum)))
        self.trainAccuracies.append(J)
        return J

    def visualize(self):
        'visualize hidden unit feature'
        spi.savemat("w2.mat", {"w2": self.W2[:, 1:]})
        # reg = np.sum(np.square(self.W2[:, 1:]), axis=1)
        # reg = reg.reshape(reg.size, 1)
        # visData = 1 / reg * self.W2[:, 1:]

        # spi.savemat("visdata.mat", {"visdata": visData})
        # k = 0
        # for element in visData:
        #     length = int(np.sqrt(element.shape[0]))
        #     element = element.reshape(length, length)
        #     element = element * 255
        #     element = element.astype('uint8')
        #     img = Image.new("L", (length, length))
        #     for i in range(length):
        #         for j in range(length):
        #             img.putpixel((i, j), element[i, j])
        #     else:
        #         img.save("bmp/vis{:02d}.bmp".format(k))
        #         k += 1

    def propagation(self, w2, w3, type=None):
        'propagation in network'

        inputdata = np.concatenate((np.ones((1, self.inData.shape[1])), self.inData), axis=0)

        u2 = w2.dot(inputdata)

        x2 = activation_func(u2)
        x2 = np.concatenate((np.ones((1, x2.shape[1])), x2), axis=0)

        # rho^
        self.activeNum = np.mean(x2[1:,:], axis=1)

        u3 = w3.dot(x2)
        x3 = activation_func(u3)
        xs = (inputdata, x2, x3)
        us = (u2, u3)
        if type is None:
            return x3
        else:
            return (xs, us)

    def backpropagation(self, args):
        'propagation in network and return gradient'
        w2 = args[0:self.W2.size]
        w3 = args[self.W2.size:]
        w2 = w2.reshape(self.W2.shape[0], self.W2.shape[1])
        w3 = w3.reshape(self.W3.shape[0], self.W3.shape[1])

        xs, us = self.propagation(w2, w3, 'forBP')

        x1, x2, x3 = xs
        u2, u3 = us

        m = x1.shape[1]

        gradEx3 = x3 - self.outData
        gradW3 = 1/m * (gradEx3 * activation_difffunc(u3)).dot(x2.transpose())

        # regularization
        regW3 = np.hstack((np.zeros((gradW3.shape[0], 1)), w3[:, 1:]))
        gradW3 += self.lam * regW3

        gradEx2 = w3.transpose().dot(gradEx3 * activation_difffunc(u3))
        # bias項のぶんだけ除く add term for sparse
        sparseTerm = self.beta * (-self.rho/self.activeNum + (1 - self.rho)/(1 - self.activeNum))
        sparseTerm = sparseTerm.reshape(sparseTerm.size, 1)

        gradW2 = 1/m * ((gradEx2[1:] + sparseTerm) * activation_difffunc(u2)).dot(x1.transpose())

        #regularization
        regW2 = np.hstack((np.zeros((gradW2.shape[0], 1)), w2[:, 1:]))
        gradW2 += self.lam * regW2

        return np.concatenate((gradW2.flatten(), gradW3.flatten()))

    def numericalGrad(self, args):
        '''get weights gradient by numerical way.
            this is only for checking, so please do not use.
        '''
        w2 = args[0:self.W2.size]
        w3 = args[self.W2.size:]
        w2 = w2.reshape(self.W2.shape[0], self.W2.shape[1])
        w3 = w3.reshape(self.W3.shape[0], self.W3.shape[1])

        ngradW2 = np.zeros(w2.shape)
        ngradW3 = np.zeros(w3.shape)
        delta = 1e-6
        originW2 = w2.copy()
        originW3 = w3.copy()

        for i in range(w2.shape[0]):
            for j in range(w2.shape[1]):
                w2[i][j] += delta
                argsNew = np.concatenate((w2.flatten(), w3.flatten()))
                upper = self.cost(argsNew)
                w2 = originW2.copy()
                w2[i][j] -= delta
                argsNew = np.concatenate((w2.flatten(), w3.flatten()))
                lower = self.cost(argsNew)
                ngradW2[i][j] = (upper - lower) / (2 * delta)
                w2 = originW2.copy()

        for i in range(w3.shape[0]):
            for j in range(w3.shape[1]):
                w3[i][j] += delta
                argsNew = np.concatenate((w2.flatten(), w3.flatten()))
                upper = self.cost(argsNew)
                w3 = originW3.copy()
                w3[i][j] -= delta
                argsNew = np.concatenate((w2.flatten(), w3.flatten()))
                lower = self.cost(argsNew)
                ngradW3[i][j] = (upper - lower) / (2 * delta)
                w3 = originW3.copy()

        return np.concatenate((ngradW2.flatten(), ngradW3.flatten()))


    def checkgrad(self, args):
        'check gradient of weights'
        bresult = self.backpropagation(args)
        w2 = bresult[0:self.W2.size]
        w3 = bresult[self.W2.size:]
        bgradW2 = w2.reshape(self.W2.shape[0], self.W2.shape[1])
        bgradW3 = w3.reshape(self.W3.shape[0], self.W3.shape[1])
        print("backp end")

        nresult = self.numericalGrad(args)
        w2 = nresult[0:self.W2.size]
        w3 = nresult[self.W2.size:]
        ngradW2 = w2.reshape(self.W2.shape[0], self.W2.shape[1])
        ngradW3 = w3.reshape(self.W3.shape[0], self.W3.shape[1])
        print("numerical end")

        print(bgradW2.shape)
        print(bgradW2)
        print(ngradW2.shape)
        print(ngradW2)
        print(np.sum(np.square(bgradW2 - ngradW2)))

        print(bgradW3.shape)
        print(bgradW3)
        print(ngradW3.shape)
        print(ngradW3)
        print(np.sum(np.square(bgradW3 - ngradW3)))
        input()

    def plot(self, type='global'):
        'plot train accuracies and test accuracies'

        print(self.trainAccuracies[-1])
        # print(self.testAccuracies[-1])

        if type == 'global':
            plt.plot(range(len(self.trainAccuracies)), self.trainAccuracies, label='train')
            # plt.plot(range(self.MaxEpoch), self.testAccuracies, label='test')
        else:
            plt.plot(range(10, self.MaxEpoch), self.trainAccuracies[10:], label='train')
            # plt.plot(range(10, self.MaxEpoch), self.testAccuracies[10:], label='test')

        plt.legend(loc='upper right')
        plt.xlabel('Epoch')
        plt.ylabel('Error')
        plt.savefig('figure.eps')
        # plt.show()
