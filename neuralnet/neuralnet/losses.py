"""Loss functions. `derivative` returns dLoss/dPrediction as a Matrix, ready
to be fed straight into the last layer's backward() call.
"""

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
