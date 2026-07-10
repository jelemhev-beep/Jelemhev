from .activations import Activation, Softmax
from .linalg import Matrix


class Dense:
    """A fully-connected layer: output = activation(input @ weights + bias)."""

    def __init__(
        self,
        input_size: int,
        output_size: int,
        activation: Activation | Softmax,
        momentum: float = 0.0,
    ):
        # Small random init keeps pre-activations near zero so sigmoid/tanh
        # don't saturate immediately.
        scale = (1.0 / input_size) ** 0.5
        self.weights = Matrix.random(input_size, output_size, scale=scale)
        self.bias = Matrix.zeros(1, output_size)
        self.activation = activation
        self.momentum = momentum
        self.velocity_w = Matrix.zeros(input_size, output_size)
        self.velocity_b = Matrix.zeros(1, output_size)
        self._input: Matrix | None = None
        self._output: Matrix | None = None

    def forward(self, x: Matrix) -> Matrix:
        self._input = x
        z = x.matmul(self.weights).add_row_broadcast(self.bias)
        if isinstance(self.activation, Softmax):
            self._output = z.softmax_rows()
        else:
            self._output = z.apply(self.activation.fn)
        return self._output

    def backward(self, grad_output: Matrix, learning_rate: float) -> Matrix:
        """grad_output is dLoss/d(this layer's output). Returns dLoss/d(this
        layer's input) so the previous layer can keep propagating it back."""
        if self._input is None or self._output is None:
            raise RuntimeError("backward() called before forward()")

        if isinstance(self.activation, Softmax):
            # dLoss/dz already simplified by losses.CROSS_ENTROPY's
            # derivative (see its docstring) -- no elementwise Jacobian here.
            grad_z = grad_output
        else:
            local_derivative = self._output.apply(self.activation.derivative)
            grad_z = grad_output.hadamard(local_derivative)

        grad_weights = self._input.transpose().matmul(grad_z)
        grad_bias = grad_z.sum_rows()
        grad_input = grad_z.matmul(self.weights.transpose())

        self.velocity_w = self.velocity_w.scale(self.momentum).sub(grad_weights.scale(learning_rate))
        self.velocity_b = self.velocity_b.scale(self.momentum).sub(grad_bias.scale(learning_rate))
        self.weights = self.weights.add(self.velocity_w)
        self.bias = self.bias.add(self.velocity_b)

        return grad_input

    def to_dict(self) -> dict:
        return {
            "weights": self.weights.data,
            "bias": self.bias.data,
            "activation": self.activation.name,
        }

    @staticmethod
    def from_dict(d: dict) -> "Dense":
        from .activations import BY_NAME

        layer = Dense.__new__(Dense)
        layer.weights = Matrix(d["weights"])
        layer.bias = Matrix(d["bias"])
        layer.activation = BY_NAME[d["activation"]]
        layer.momentum = 0.0
        layer.velocity_w = Matrix.zeros(layer.weights.rows, layer.weights.cols)
        layer.velocity_b = Matrix.zeros(1, layer.bias.cols)
        layer._input = None
        layer._output = None
        return layer
