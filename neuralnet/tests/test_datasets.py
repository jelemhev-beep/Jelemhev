import gzip
import struct

from neuralnet.datasets import read_idx_images, read_idx_labels


def _write_idx_images(path, images: list[list[int]], rows: int, cols: int) -> None:
    with gzip.open(path, "wb") as f:
        f.write(struct.pack(">IIII", 2051, len(images), rows, cols))
        for image in images:
            f.write(bytes(image))


def _write_idx_labels(path, labels: list[int]) -> None:
    with gzip.open(path, "wb") as f:
        f.write(struct.pack(">II", 2049, len(labels)))
        f.write(bytes(labels))


def test_read_idx_images_parses_and_normalises(tmp_path):
    path = tmp_path / "images.gz"
    images = [[0, 128, 255, 64], [255, 255, 0, 0]]
    _write_idx_images(path, images, rows=2, cols=2)

    result = read_idx_images(path)
    assert len(result) == 2
    assert result[0] == [0.0, 128 / 255, 1.0, 64 / 255]
    assert result[1] == [1.0, 1.0, 0.0, 0.0]


def test_read_idx_labels_parses(tmp_path):
    path = tmp_path / "labels.gz"
    _write_idx_labels(path, [0, 1, 2, 9, 5])

    assert read_idx_labels(path) == [0, 1, 2, 9, 5]


def test_read_idx_images_rejects_wrong_magic(tmp_path):
    path = tmp_path / "bad.gz"
    with gzip.open(path, "wb") as f:
        f.write(struct.pack(">IIII", 9999, 1, 2, 2))
        f.write(bytes([0, 0, 0, 0]))

    try:
        read_idx_images(path)
        assert False, "expected ValueError for wrong magic number"
    except ValueError:
        pass
