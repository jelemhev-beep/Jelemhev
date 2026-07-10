"""Loss functions. `derivative` returns dLoss/dPrediction as a Matrix, ready
to be fed straight into the last layer's backward() call.
"""

import math
from dataclasses import dataclass
from typing import Callable

from .linalg import Matrix


@dataclass
class Loss:
    name: str
    fn: Callable[[Matrix, Matrix], float]
    derivative: Callable[[Matrix, Matrix], Matrix]


def _mse(prediction: Matrix, target: Matrix) -> float:
    diff = prediction.sub(target)
    n = diff.rows * diff.cols
    return sum(v * v for row in diff.data for v in row) / n


def _mse_derivative(prediction: Matrix, target: Matrix) -> Matrix:
    diff = prediction.sub(target)
    n = diff.rows * diff.cols
    return diff.scale(2.0 / n)


MSE = Loss("mse", _mse, _mse_derivative)


def _cross_entropy(prediction: Matrix, target: Matrix) -> float:
    eps = 1e-12
    total = 0.0
    for p_row, t_row in zip(prediction.data, target.data):
        for p, t in zip(p_row, t_row):
            total -= t * math.log(max(p, eps))
    return total / prediction.rows


def _cross_entropy_derivative(prediction: Matrix, target: Matrix) -> Matrix:
    """Only valid when `prediction` is the output of a SOFTMAX layer: the
    combined softmax+cross-entropy gradient simplifies to (prediction -
    target) / batch_size. Pairing cross-entropy with any other output
    activation would need a different derivative.
    """
    diff = prediction.sub(target)
    return diff.scale(1.0 / prediction.rows)


CROSS_ENTROPY = Loss("cross_entropy", _cross_entropy, _cross_entropy_derivative)
