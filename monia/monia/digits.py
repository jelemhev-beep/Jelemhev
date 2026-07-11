"""Bridges to the `neuralnet` project (a sibling folder in the same repo)
to reuse its digit-drawing canvas and trained classifier as a MonIA
command, instead of re-implementing a neural network inside MonIA too.
"""

import sys
from pathlib import Path

_NEURALNET_ROOT = Path(__file__).resolve().parent.parent.parent / "neuralnet"


class NeuralnetUnavailable(Exception):
    pass


def _import_neuralnet():
    if not _NEURALNET_ROOT.exists():
        raise NeuralnetUnavailable(
            f"Le projet neuralnet est introuvable a {_NEURALNET_ROOT}. "
            "Il doit etre clone a cote de monia (dossiers freres dans le meme depot)."
        )
    if str(_NEURALNET_ROOT) not in sys.path:
        sys.path.insert(0, str(_NEURALNET_ROOT))
    from examples import draw as draw_module
    from neuralnet.network import Network

    return draw_module, Network


def default_model_path() -> Path:
    return _NEURALNET_ROOT / "mnist_model_v2.json"


def run_digit_session(model_path: str | None = None, input_lines=None) -> str | None:
    """Runs the neuralnet drawing tool inline. Returns a short text summary
    of the last prediction made (to save in the second brain), or None if
    the session ended without ever calling 'predict'.
    """
    draw_module, network_cls = _import_neuralnet()

    path = model_path or str(default_model_path())
    try:
        network = network_cls.load(path)
    except FileNotFoundError as exc:
        raise NeuralnetUnavailable(
            f"Modele introuvable : {path}. Lance d'abord "
            "neuralnet/examples/mnist.py (ou mnist_improved.py) pour en creer un."
        ) from exc

    print(f"Modele charge : {path}")
    print(draw_module.HELP)

    last_result: list[str | None] = [None]

    def on_predict(digit: int, confidence: float) -> None:
        last_result[0] = f"Chiffre dessine reconnu : {digit} (confiance {confidence:.1%})"

    draw_module.run(network, input_lines=input_lines, on_predict=on_predict)

    return last_result[0]
