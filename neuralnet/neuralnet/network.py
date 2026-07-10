import json

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
        verbose: bool = False,
        log_every: int = 100,
    ) -> list[float]:
        history = []
        for epoch in range(1, epochs + 1):
            loss_value = self.train_step(x, y, learning_rate)
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
        from .losses import MSE

        with open(path) as f:
            payload = json.load(f)
        layers = [Dense.from_dict(d) for d in payload["layers"]]
        loss = {"mse": MSE}[payload["loss"]]
        return Network(layers, loss)
