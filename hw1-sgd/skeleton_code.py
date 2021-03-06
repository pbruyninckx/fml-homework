import pandas as pd
import logging
import numpy as np
import sys
from typing import List, Union
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

# Assignment Owner: Tian Wang

#######################################
# Normalization


def feature_normalization(train, test):
    """Rescale the data so that each feature in the training set is in
    the interval [0,1], and apply the same transformations to the test
    set, using the statistics computed on the training set.

    Args:
        train - training set, a 2D numpy array of size (num_instances, num_features)
        test  - test set, a 2D numpy array of size (num_instances, num_features)
    Returns:
        train_normalized - training set after normalization
        test_normalized  - test set after normalization

    """
    train_min = train.min(axis=0)
    train_max = train.max(axis=0)
    discard = train_min == train_max
    train_min = np.delete(train_min, discard)
    train_max = np.delete(train_max, discard)
    train_normalized = np.delete(train, discard, axis=1)
    train_normalized = (train_normalized-train_min)/(train_max-train_min)
    test_normalized = np.delete(test, discard, axis=1)
    test_normalized = (test_normalized-train_min)/(train_max - train_min)
    return train_normalized, test_normalized


########################################
# The square loss function

def compute_square_loss(X, y, theta):
    """
    Given a set of X, y, theta, compute the square loss for predicting y with X*theta

    Args:
        X - the feature vector, 2D numpy array of size (num_instances, num_features)
        y - the label vector, 1D numpy array of size (num_instances)
        theta - the parameter vector, 1D array of size (num_features)

    Returns:
        loss - the square loss, scalar
    """
    m = X.shape[0]
    distance_vector = np.matmul(X, theta) - y
    loss = 1/m * np.matmul(distance_vector.transpose(), distance_vector)
    return loss


########################################
# compute the gradient of square loss function
def compute_square_loss_gradient(X: np.ndarray, y: np.ndarray, theta: np.ndarray):
    """
    Compute gradient of the square loss (as defined in compute_square_loss), at the point theta.

    Args:
        X - the feature vector, 2D numpy array of size (num_instances, num_features)
        y - the label vector, 1D numpy array of size (num_instances)
        theta - the parameter vector, 1D numpy array of size (num_features)

    Returns:
        grad - gradient vector, 1D numpy array of size (num_features)
    """
    m = X.shape[0]
    grad = 2/m * np.matmul(X.transpose(), (np.matmul(X, theta) - y))
    return grad


###########################################
# Gradient Checker
# Getting the gradient calculation correct is often the trickiest part
# of any gradient-based optimization algorithm.  Fortunately, it's very
# easy to check that the gradient calculation is correct using the
# definition of gradient.
# See http://ufldl.stanford.edu/wiki/index.php/Gradient_checking_and_advanced_optimization
def grad_checker(X: np.ndarray, y: np.ndarray, theta: np.ndarray, epsilon=0.01, tolerance=1e-4):
    """Implement Gradient Checker
    Check that the function compute_square_loss_gradient returns the
    correct gradient for the given X, y, and theta.

    Let d be the number of features. Here we numerically estimate the
    gradient by approximating the directional derivative in each of
    the d coordinate directions:
    (e_1 = (1,0,0,...,0), e_2 = (0,1,0,...,0), ..., e_d = (0,...,0,1)

    The approximation for the directional derivative of J at the point
    theta in the direction e_i is given by:
    ( J(theta + epsilon * e_i) - J(theta - epsilon * e_i) ) / (2*epsilon).

    We then look at the Euclidean distance between the gradient
    computed using this approximation and the gradient computed by
    compute_square_loss_gradient(X, y, theta).  If the Euclidean
    distance exceeds tolerance, we say the gradient is incorrect.

    Args:
        X - the feature vector, 2D numpy array of size (num_instances, num_features)
        y - the label vector, 1D numpy array of size (num_instances)
        theta - the parameter vector, 1D numpy array of size (num_features)
        epsilon - the epsilon used in approximation
        tolerance - the tolerance error

    Return:
        A boolean value indicate whether the gradient is correct or not

    """
    true_gradient = compute_square_loss_gradient(X, y, theta)  # the true gradient
    num_features = theta.shape[0]
    approx_grad = np.zeros(num_features)  # Initialize the gradient we approximate
    identity = np.identity(num_features)
    for dim in range(num_features):
        h = identity[dim]
        approx_grad[dim] = compute_square_loss(X, y, theta + epsilon * h) \
            - compute_square_loss(X, y, theta - epsilon * h)
    approx_grad /= 2 * epsilon
    distance = np.linalg.norm(true_gradient - approx_grad)
    return distance < tolerance


#################################################
# Generic Gradient Checker
def generic_gradient_checker(X, y, theta, objective_func, gradient_func, epsilon=0.01, tolerance=1e-4):
    """
    The functions takes objective_func and gradient_func as parameters. And check whether gradient_func(X, y, theta) returned
    the true gradient for objective_func(X, y, theta).
    Eg: In LSR, the objective_func = compute_square_loss, and gradient_func = compute_square_loss_gradient
    """
    true_gradient = gradient_func(X, y, theta)  # the true gradient
    num_features = theta.shape[0]
    approx_grad = np.zeros(num_features)  # Initialize the gradient we approximate
    identity = np.identity(num_features)
    for dim in range(num_features):
        h = identity[dim]
        approx_grad[dim] = objective_func(theta + epsilon * h) - objective_func(theta - epsilon * h)
    approx_grad /= 2 * epsilon
    distance = np.linalg.norm(true_gradient - approx_grad)
    return distance < tolerance


####################################
# Batch Gradient Descent
def batch_grad_descent(X: np.ndarray, y: np.ndarray, alpha=0.1, num_iter=1000, check_gradient=False):
    """
    In this question you will implement batch gradient descent to
    minimize the square loss objective

    Args:
        X - the feature vector, 2D numpy array of size (num_instances, num_features)
        y - the label vector, 1D numpy array of size (num_instances)
        alpha - step size in gradient descent
        num_iter - number of iterations to run
        check_gradient - a boolean value indicating whether checking the gradient when updating

    Returns:
        theta_hist - store the the history of parameter vector in iteration, 2D numpy array of size (num_iter+1, num_features)
                    for instance, theta in iteration 0 should be theta_hist[0], theta in iteration (num_iter) is theta_hist[-1]
        loss_hist - the history of objective function vector, 1D numpy array of size (num_iter+1)
    """
    num_instances, num_features = X.shape[0], X.shape[1]
    theta_hist = np.zeros((num_iter+1, num_features))  # Initialize theta_hist
    loss_hist = np.zeros(num_iter+1)  # initialize loss_hist
    theta = np.zeros(num_features)  # initialize theta
    for cur_iter in range(num_iter+1):
        loss_hist[cur_iter] = compute_square_loss(X, y, theta)
        theta_hist[cur_iter] = theta
        if check_gradient and not grad_checker(X, y, theta):
            print("Error in gradient at iteration {}".format(cur_iter), file=sys.stderr)
        theta -= alpha * compute_square_loss_gradient(X, y, theta)
    return theta_hist, loss_hist


####################################
# Q2.4b: Implement backtracking line search in batch_gradient_descent
# Check http://en.wikipedia.org/wiki/Backtracking_line_search for details
def batch_grad_descent_with_btl(X: np.ndarray, y: np.ndarray, alpha0: float = 1, num_iter=1000, c=0.5, tau=0.5):
    num_features = X.shape[1]
    theta = np.zeros(num_features)
    loss_hist = np.zeros(num_iter+1)
    loss_hist[0] = compute_square_loss(X, y, theta)
    for cur_iter in range(1, num_iter+1):
        gradient = compute_square_loss_gradient(X, y, theta)
        p = - gradient / np.linalg.norm(gradient)
        m = np.dot(gradient, p)
        assert (m < 0)
        t = -c * m
        alpha = alpha0
        while True:
            loss_hist[cur_iter] = compute_square_loss(X, y, theta + alpha*p)
            improvement = loss_hist[cur_iter-1] - loss_hist[cur_iter]
            if improvement >= alpha * t:
                theta += alpha*p
                break
            alpha *= tau
    return loss_hist


###################################################
# Compute the gradient of Regularized Batch Gradient Descent
def compute_regularized_square_loss_gradient(X, y, theta, lambda_reg):
    """
    Compute the gradient of L2-regularized square loss function given X, y and theta

    Args:
        X - the feature vector, 2D numpy array of size (num_instances, num_features)
        y - the label vector, 1D numpy array of size (num_instances)
        theta - the parameter vector, 1D numpy array of size (num_features)
        lambda_reg - the regularization coefficient

    Returns:
        grad - gradient vector, 1D numpy array of size (num_features)
    """
    m = X.shape[0]
    grad = 2/m * np.matmul(X.transpose(), (np.matmul(X, theta) - y)) + 2 * lambda_reg * theta
    return grad


###################################################
# Batch Gradient Descent with regularization term
def regularized_grad_descent(X: np.ndarray, y: np.ndarray, alpha=0.1, lambda_reg=1, num_iter=1000):
    """
    Args:
        X - the feature vector, 2D numpy array of size (num_instances, num_features)
        y - the label vector, 1D numpy array of size (num_instances)
        alpha - step size in gradient descent
        lambda_reg - the regularization coefficient
        numIter - number of iterations to run

    Returns:
        theta_hist - the history of parameter vector, 2D numpy array of size (num_iter+1, num_features)
        loss_hist - the history of loss function without the regularization term, 1D numpy array.
    """

    def J(cur_theta: np.ndarray):
        return compute_square_loss(X, y, cur_theta) + lambda_reg * np.dot(cur_theta, cur_theta)

    (num_instances, num_features) = X.shape
    theta = np.zeros(num_features)  # Initialize theta
    theta_hist = np.zeros((num_iter + 1, num_features))  # Initialize theta_hist
    loss_hist = np.zeros(num_iter + 1)  # Initialize loss_hist
    for cur_iter in range(num_iter+1):
        loss_hist[cur_iter] = J(theta)
        theta_hist[cur_iter] = theta
        theta -= alpha * compute_regularized_square_loss_gradient(X, y, theta, lambda_reg)
    return theta_hist, loss_hist


#############################################
## Visualization of Regularized Batch Gradient Descent
##X-axis: log(lambda_reg)
##Y-axis: square_loss

#############################################
# Stochastic Gradient Descent
def stochastic_grad_descent(X: np.ndarray, y: np.ndarray, alpha: Union[float, str] = 0.1, lambda_reg: float = 1,
                            num_iter: int = 1000) -> (np.ndarray, np.ndarray):
    """
    In this question you will implement stochastic gradient descent with a regularization term

    Args:
        X: the feature vector, 2D numpy array of size (num_instances, num_features)
        y: the label vector, 1D numpy array of size (num_instances)
        alpha:  string or float. step size in gradient descent
                NOTE: In SGD, it's not always a good idea to use a fixed step size. Usually it's set to 1/sqrt(t) or 1/t
                if alpha is a float, then the step size in every iteration is alpha.
                if alpha == "1/sqrt(t)", alpha = 1/sqrt(t)
                if alpha == "1/t", alpha = 1/t
        lambda_reg: the regularization coefficient
        num_iter: number of epochs (i.e number of times) to go through the whole training set

    Returns:
        theta_hist - the history of parameter vector, 3D numpy array of size (num_iter, num_instances, num_features)
        loss_hist - the history of regularized loss function vector, 2D numpy array of size(num_iter, num_instances)
    """
    num_instances, num_features = X.shape[0], X.shape[1]
    theta = np.ones(num_features)  # Initialize theta

    theta_hist = np.zeros((num_iter, num_instances, num_features))  # Initialize theta_hist
    loss_hist = np.zeros((num_iter, num_instances))  # Initialize loss_hist

    def J(cur_theta: np.ndarray):
        return compute_square_loss(X, y, cur_theta) + lambda_reg * np.dot(cur_theta, cur_theta)

    if alpha == "1/sqrt(t)":
        def eta(t):
            return min(0.02, 1.0 / np.sqrt(t+10))
    elif alpha == "1/t":
        def eta(t):
            return min(0.02, 1.0 / (t + 10))
    else:
        def eta(_):
            return alpha
        assert isinstance(alpha, float)

    for cur_iter in range(num_iter):
        # Assuming the instances are in random order
        for cur_instance in range(num_instances):
            theta -= eta(cur_iter) * 2 * (X[cur_instance] * (np.dot(theta, X[cur_instance]) - y[cur_instance])
                                          + lambda_reg * theta)
            theta_hist[cur_iter, cur_instance] = theta
            loss_hist[cur_iter, cur_instance] = J(theta)

    return theta_hist, loss_hist


################################################
### Visualization that compares the convergence speed of batch
###and stochastic gradient descent for various approaches to step_size
##X-axis: Step number (for gradient descent) or Epoch (for SGD)
##Y-axis: log(objective_function_value) and/or objective_function_value

def main():
    # Loading the dataset
    print('loading the dataset')

    df = pd.read_csv('data.csv', delimiter=',')
    X = df.values[:, :-1]
    y = df.values[:, -1]

    print('Split into Train and Test')
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=100, random_state=10)

    print("Scaling all to [0, 1]")
    X_train, X_test = feature_normalization(X_train, X_test)
    X_train = np.hstack((X_train, np.ones((X_train.shape[0], 1))))  # Add bias term
    X_test = np.hstack((X_test, np.ones((X_test.shape[0], 1)))) # Add bias term

    # plot_step_size_effect(X_train, y_train)

    # ridge_regression_ex(X_train, y_train, X_test, y_test)

    stochastic_gradient_descent_ex(X_train, y_train, X_test, y_test)

def ridge_regression_ex(X_train, y_train, X_test, y_test):
    """
    Do some experiments to find an optimal value for the regularization parameter lambda
    """
    lambda_regs = np.logspace(-2, -1, 10)
    num_lambda_regs = len(lambda_regs)
    J_train = np.zeros(num_lambda_regs)
    J_test = np.zeros(num_lambda_regs)

    for ind, lambda_reg in enumerate(lambda_regs):
        theta_hist, _ = regularized_grad_descent(X_train, y_train, 0.02, lambda_reg, 2000)
        theta = theta_hist[-1]
        J_train[ind] = compute_square_loss(X_train, y_train, theta)
        J_test[ind] = compute_square_loss(X_test, y_test, theta)
    plt.figure()
    plt.plot(lambda_regs, J_train, label="training loss")
    plt.plot(lambda_regs, J_test, label="test loss")
    plt.legend()
    plt.semilogx()
    plt.xlabel("Regularization (λ)")
    plt.ylabel("Loss")


def stochastic_gradient_descent_ex(X_train, y_train, X_test, y_test):
    """
    Do some experiments with the stochastic gradient descent.
    """
    lambda_reg = 0.025
    etas = [0.025, 0.01, 0.005, "1/t", "1/sqrt(t)"]
    num_etas = len(etas)
    J_train = np.zeros(num_etas)
    J_test = np.zeros(num_etas)

    for ind, eta in enumerate(etas):
        theta_hist, loss_hist = stochastic_grad_descent(X_train, y_train, eta, lambda_reg, 1000)
        theta_hist = theta_hist[:, -1, :]
        plt.figure()
        plt.plot(loss_hist[:, -1], label=eta)
        theta = theta_hist[-1]
        J_train[ind] = compute_square_loss(X_train, y_train, theta)
        J_test[ind] = compute_square_loss(X_test, y_test, theta)
    plt.figure()
    plt.plot(J_train, label="training loss")
    plt.plot(J_test, label="test loss")
    plt.legend()
    plt.xlabel("eta")
    plt.ylabel("Loss")


def plot_step_size_effect(X, y):
    for step_size in [.5, .1, .05, .01]:
        theta_hist, loss_hist = batch_grad_descent(X, y, step_size)
        plt.plot(loss_hist, label="step size {}".format(step_size))
    loss_hist = batch_grad_descent_with_btl(X, y, .1)
    plt.figure()
    plt.plot(loss_hist, label="backtracking line search")
    # Rescale y-axis
    cur_axis = list(plt.axis())
    cur_axis[2:4] = [0, 10]
    plt.axis(cur_axis)
    plt.legend()
    plt.xlabel("iteration")
    plt.ylabel("loss")


if __name__ == "__main__":
    main()
