import pytest

from neuralnet.linalg import Matrix, ShapeError


def test_matmul():
    a = Matrix([[1, 2], [3, 4]])
    b = Matrix([[5, 6], [7, 8]])
    result = a.matmul(b)
    assert result.data == [[19, 22], [43, 50]]


def test_matmul_shape_mismatch_raises():
    a = Matrix([[1, 2, 3]])
    b = Matrix([[1, 2]])
    with pytest.raises(ShapeError):
        a.matmul(b)


def test_transpose():
    a = Matrix([[1, 2, 3], [4, 5, 6]])
    t = a.transpose()
    assert t.data == [[1, 4], [2, 5], [3, 6]]
    assert t.rows == 3 and t.cols == 2


def test_add_and_sub():
    a = Matrix([[1, 2], [3, 4]])
    b = Matrix([[10, 10], [10, 10]])
    assert a.add(b).data == [[11, 12], [13, 14]]
    assert b.sub(a).data == [[9, 8], [7, 6]]


def test_add_row_broadcast():
    a = Matrix([[1, 2], [3, 4], [5, 6]])
    bias = Matrix([[100, 200]])
    result = a.add_row_broadcast(bias)
    assert result.data == [[101, 202], [103, 204], [105, 206]]


def test_hadamard():
    a = Matrix([[1, 2], [3, 4]])
    b = Matrix([[2, 2], [2, 2]])
    assert a.hadamard(b).data == [[2, 4], [6, 8]]


def test_scale():
    a = Matrix([[1, 2], [3, 4]])
    assert a.scale(2).data == [[2, 4], [6, 8]]


def test_apply():
    a = Matrix([[1, 2], [3, 4]])
    assert a.apply(lambda v: v * v).data == [[1, 4], [9, 16]]


def test_sum_rows():
    a = Matrix([[1, 2, 3], [4, 5, 6]])
    result = a.sum_rows()
    assert result.rows == 1
    assert result.data == [[5, 7, 9]]


def test_empty_matrix_rejected():
    with pytest.raises(ShapeError):
        Matrix([])


def test_ragged_matrix_rejected():
    with pytest.raises(ShapeError):
        Matrix([[1, 2], [3]])
