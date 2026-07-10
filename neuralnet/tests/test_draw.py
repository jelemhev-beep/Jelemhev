import pytest

from examples.draw import SIZE, bresenham, new_grid, render, run, set_pixel
from neuralnet.activations import SIGMOID, SOFTMAX
from neuralnet.layer import Dense
from neuralnet.losses import CROSS_ENTROPY
from neuralnet.network import Network


def test_bresenham_horizontal_line():
    assert bresenham(0, 0, 0, 4) == [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]


def test_bresenham_vertical_line():
    assert bresenham(0, 0, 4, 0) == [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]


def test_set_pixel_lights_center_and_soft_neighbors():
    grid = new_grid()
    set_pixel(grid, 5, 5, intensity=1.0)
    assert grid[5][5] == 1.0
    assert grid[4][5] == pytest.approx(0.4)
    assert grid[6][5] == pytest.approx(0.4)
    assert grid[5][4] == pytest.approx(0.4)
    assert grid[5][6] == pytest.approx(0.4)
    assert grid[0][0] == 0.0  # untouched, far from the drawn pixel


def test_set_pixel_out_of_bounds_is_ignored():
    grid = new_grid()
    set_pixel(grid, -1, 0)  # must not raise or wrap around
    set_pixel(grid, SIZE, SIZE)
    assert all(v == 0.0 for row in grid for v in row)


def test_render_has_correct_dimensions():
    lines = render(new_grid()).splitlines()
    assert len(lines) == SIZE + 1  # header row + one row per grid line


def _tiny_network() -> Network:
    return Network(layers=[Dense(784, 8, SIGMOID), Dense(8, 10, SOFTMAX)], loss=CROSS_ENTROPY)


def test_run_predict_command_outputs_probabilities(capsys):
    run(_tiny_network(), ["set 5 5", "predict", "quit"])
    out = capsys.readouterr().out
    assert "Prediction" in out
    assert "%" in out


def test_run_clear_and_unknown_command(capsys):
    run(_tiny_network(), ["set 1 1", "clear", "unknowncmd", "quit"])
    out = capsys.readouterr().out
    assert "Grille effacee" in out
    assert "Commande inconnue" in out


def test_run_line_command_draws_and_shows(capsys):
    run(_tiny_network(), ["line 0 0 0 4", "show", "quit"])
    out = capsys.readouterr().out
    # header + 28 grid rows for the "show" output (plus one more render
    # triggered by the "line" command itself)
    assert out.count("0123456789") >= 1
