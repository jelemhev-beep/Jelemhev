"""Activation functions. Each derivative is expressed in terms of the
activation's own OUTPUT (not its input), which is the standard trick that
avoids recomputing the forward pass during backpropagation.
"""

import math
from dataclasses import dataclass
from typing import Callable


@dataclass
class Activation:
    name: str
    fn: Callable[[float], float]
    derivative: Callable[[float], float]  # takes the output value, returns d(output)/d(input)


def _sigmoid(x: float) -> float:
    # numerically stable sigmoid, avoids overflow in math.exp for very negative x
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _sigmoid_derivative(output: float) -> float:
    return output * (1.0 - output)


def _tanh(x: float) -> float:
    return math.tanh(x)


def _tanh_derivative(output: float) -> float:
    return 1.0 - output * output


def _relu(x: float) -> float:
    return x if x > 0.0 else 0.0


def _relu_derivative(output: float) -> float:
    return 1.0 if output > 0.0 else 0.0


def _identity(x: float) -> float:
    return x


def _identity_derivative(_output: float) -> float:
    return 1.0


SIGMOID = Activation("sigmoid", _sigmoid, _sigmoid_derivative)
TANH = Activation("tanh", _tanh, _tanh_derivative)
RELU = Activation("relu", _relu, _relu_derivative)
LINEAR = Activation("linear", _identity, _identity_derivative)

BY_NAME = {a.name: a for a in (SIGMOID, TANH, RELU, LINEAR)}
