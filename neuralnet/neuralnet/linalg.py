"""Minimal matrix type backed by plain Python lists. No numpy: every
operation is a manual nested loop, which is the point of this project.
"""

import math
import random


class ShapeError(Exception):
    pass


class Matrix:
    def __init__(self, data: list[list[float]]):
        if not data or not data[0]:
            raise ShapeError("Matrix cannot be empty")
        width = len(data[0])
        if any(len(row) != width for row in data):
            raise ShapeError("All rows must have the same length")
        self.data = data
        self.rows = len(data)
        self.cols = width

    @staticmethod
    def zeros(rows: int, cols: int) -> "Matrix":
        return Matrix([[0.0] * cols for _ in range(rows)])

    @staticmethod
    def random(rows: int, cols: int, scale: float = 1.0) -> "Matrix":
        return Matrix([[random.uniform(-scale, scale) for _ in range(cols)] for _ in range(rows)])

    @staticmethod
    def from_rows(rows: list[list[float]]) -> "Matrix":
        return Matrix([list(row) for row in rows])

    def _check_same_shape(self, other: "Matrix") -> None:
        if self.rows != other.rows or self.cols != other.cols:
            raise ShapeError(
                f"Shape mismatch: {self.rows}x{self.cols} vs {other.rows}x{other.cols}"
            )

    def add(self, other: "Matrix") -> "Matrix":
        self._check_same_shape(other)
        return Matrix(
            [[self.data[i][j] + other.data[i][j] for j in range(self.cols)] for i in range(self.rows)]
        )

    def add_row_broadcast(self, row: "Matrix") -> "Matrix":
        """Add a 1xN row (e.g. a bias vector) to every row of this matrix."""
        if row.rows != 1 or row.cols != self.cols:
            raise ShapeError(f"Cannot broadcast {row.rows}x{row.cols} onto {self.rows}x{self.cols}")
        return Matrix(
            [[self.data[i][j] + row.data[0][j] for j in range(self.cols)] for i in range(self.rows)]
        )

    def sub(self, other: "Matrix") -> "Matrix":
        self._check_same_shape(other)
        return Matrix(
            [[self.data[i][j] - other.data[i][j] for j in range(self.cols)] for i in range(self.rows)]
        )

    def hadamard(self, other: "Matrix") -> "Matrix":
        """Elementwise product."""
        self._check_same_shape(other)
        return Matrix(
            [[self.data[i][j] * other.data[i][j] for j in range(self.cols)] for i in range(self.rows)]
        )

    def scale(self, scalar: float) -> "Matrix":
        return Matrix([[v * scalar for v in row] for row in self.data])

    def matmul(self, other: "Matrix") -> "Matrix":
        if self.cols != other.rows:
            raise ShapeError(
                f"Cannot multiply {self.rows}x{self.cols} by {other.rows}x{other.cols}"
            )
        other_t = other.transpose()
        return Matrix(
            [
                [sum(a * b for a, b in zip(self_row, other_row)) for other_row in other_t.data]
                for self_row in self.data
            ]
        )

    def transpose(self) -> "Matrix":
        return Matrix([[self.data[i][j] for i in range(self.rows)] for j in range(self.cols)])

    def apply(self, fn) -> "Matrix":
        return Matrix([[fn(v) for v in row] for row in self.data])

    def sum_rows(self) -> "Matrix":
        """Collapse a rows x cols matrix into a 1 x cols matrix by summing
        down each column (used to sum gradients over a batch)."""
        totals = [0.0] * self.cols
        for row in self.data:
            for j, v in enumerate(row):
                totals[j] += v
        return Matrix([totals])

    def sum(self) -> float:
        return sum(v for row in self.data for v in row)

    def select_rows(self, indices: list[int]) -> "Matrix":
        return Matrix([self.data[i] for i in indices])

    def softmax_rows(self) -> "Matrix":
        """Row-wise softmax. Not elementwise (each output depends on the
        whole row), so it can't go through the generic Activation interface.
        """
        result = []
        for row in self.data:
            m = max(row)
            exps = [math.exp(v - m) for v in row]
            total = sum(exps)
            result.append([e / total for e in exps])
        return Matrix(result)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Matrix):
            return NotImplemented
        return self.data == other.data

    def __repr__(self) -> str:
        return f"Matrix({self.data!r})"
