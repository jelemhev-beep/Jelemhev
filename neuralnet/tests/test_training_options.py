from neuralnet.activations import SIGMOID
from neuralnet.layer import Dense
from neuralnet.linalg import Matrix
from neuralnet.losses import MSE
from neuralnet.network import Network

X = Matrix([[0, 0], [0, 1], [1, 0], [1, 1]])
Y = Matrix([[0], [1], [1], [0]])


def test_minibatch_training_solves_xor():
    network = Network(layers=[Dense(2, 4, SIGMOID), Dense(4, 1, SIGMOID)], loss=MSE)
    network.fit(X, Y, epochs=3000, learning_rate=0.5, batch_size=2)

    predictions = network.predict(X)
    for i in range(X.rows):
        assert round(predictions.data[i][0]) == Y.data[i][0]


def test_momentum_still_converges():
    network = Network(layers=[Dense(2, 4, SIGMOID, momentum=0.9), Dense(4, 1, SIGMOID, momentum=0.9)], loss=MSE)
    history = network.fit(X, Y, epochs=3000, learning_rate=0.1)

    assert history[-1] < history[0] * 0.2
    predictions = network.predict(X)
    for i in range(X.rows):
        assert round(predictions.data[i][0]) == Y.data[i][0]


def test_zero_momentum_matches_plain_sgd_update():
    """momentum=0.0 (the default) must produce the exact same weight
    trajectory as before momentum existed -- no surprise behaviour change."""
    network_a = Network(layers=[Dense(2, 3, SIGMOID), Dense(3, 1, SIGMOID)], loss=MSE)
    network_b = Network(
        layers=[Dense(2, 3, SIGMOID, momentum=0.0), Dense(3, 1, SIGMOID, momentum=0.0)], loss=MSE
    )
    # give both networks identical starting weights
    for la, lb in zip(network_a.layers, network_b.layers):
        lb.weights = Matrix([row[:] for row in la.weights.data])
        lb.bias = Matrix([row[:] for row in la.bias.data])

    network_a.fit(X, Y, epochs=50, learning_rate=0.5)
    network_b.fit(X, Y, epochs=50, learning_rate=0.5)

    for la, lb in zip(network_a.layers, network_b.layers):
        assert la.weights.data == lb.weights.data
        assert la.bias.data == lb.bias.data
