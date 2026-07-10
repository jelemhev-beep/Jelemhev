import pytest

from neuralnet.activations import RELU, SIGMOID, TANH


def test_sigmoid_known_values():
    assert SIGMOID.fn(0.0) == pytest.approx(0.5)
    assert SIGMOID.fn(100.0) == pytest.approx(1.0)
    assert SIGMOID.fn(-100.0) == pytest.approx(0.0)


def test_sigmoid_derivative_from_output():
    # at output=0.5 (i.e. x=0), derivative should be 0.25
    assert SIGMOID.derivative(0.5) == pytest.approx(0.25)


def test_tanh_known_values():
    assert TANH.fn(0.0) == pytest.approx(0.0)
    assert TANH.fn(10.0) == pytest.approx(1.0)


def test_tanh_derivative_from_output():
    assert TANH.derivative(0.0) == pytest.approx(1.0)


def test_relu():
    assert RELU.fn(5.0) == 5.0
    assert RELU.fn(-5.0) == 0.0
    assert RELU.derivative(5.0) == 1.0
    assert RELU.derivative(0.0) == 0.0
