import json
import random

from .layer import Dense
from .linalg import Matrix
from .losses import Loss


class Network:
    def __init__(self, layers: list[Dense], loss: Loss):
        self.layers = layers
        self.loss = loss

    def predict(self, x: Matrix) -> Matrix:
        output = x
        for layer in self.layers:
            output = layer.forward(output)
        return output

    def train_step(self, x: Matrix, y: Matrix, learning_rate: float) -> float:
        prediction = self.predict(x)
        loss_value = self.loss.fn(prediction, y)

        grad = self.loss.derivative(prediction, y)
        for layer in reversed(self.layers):
            grad = layer.backward(grad, learning_rate)

        return loss_value

    def fit(
        self,
        x: Matrix,
        y: Matrix,
        epochs: int,
        learning_rate: float,
        batch_size: int | None = None,
        verbose: bool = False,
        log_every: int = 100,
    ) -> list[float]:
        """batch_size=None trains full-batch (whole dataset each step, the
        original behaviour). Any int splits each epoch into shuffled
        mini-batches, which is what makes large datasets like MNIST tractable.
        """
        history = []
        n = x.rows
        for epoch in range(1, epochs + 1):
            if batch_size is None:
                loss_value = self.train_step(x, y, learning_rate)
            else:
                indices = list(range(n))
                random.shuffle(indices)
                total_loss = 0.0
                num_batches = 0
                for start in range(0, n, batch_size):
                    batch_indices = indices[start : start + batch_size]
                    batch_x = x.select_rows(batch_indices)
                    batch_y = y.select_rows(batch_indices)
                    total_loss += self.train_step(batch_x, batch_y, learning_rate)
                    num_batches += 1
                loss_value = total_loss / num_batches

            history.append(loss_value)
            if verbose and (epoch % log_every == 0 or epoch == 1 or epoch == epochs):
                print(f"epoch {epoch:>6}/{epochs}  loss={loss_value:.6f}")
        return history

    def save(self, path: str) -> None:
        payload = {"loss": self.loss.name, "layers": [layer.to_dict() for layer in self.layers]}
        with open(path, "w") as f:
            json.dump(payload, f)

    @staticmethod
    def load(path: str) -> "Network":
        from .losses import CROSS_ENTROPY, MSE

        with open(path) as f:
            payload = json.load(f)
        layers = [Dense.from_dict(d) for d in payload["layers"]]
        loss = {"mse": MSE, "cross_entropy": CROSS_ENTROPY}[payload["loss"]]
        return Network(layers, loss)
