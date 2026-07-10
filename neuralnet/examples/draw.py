#!/usr/bin/env python3
"""Draw a digit by hand, right in the terminal, and watch the network
(trained via examples/mnist.py or mnist_improved.py) guess what it is.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neuralnet.linalg import Matrix  # noqa: E402
from neuralnet.network import Network  # noqa: E402

SIZE = 28
RAMP = " .:oO#"

HELP = """
Commandes :
  set L C [intensite]     allume le pixel (ligne L, colonne C), 0-27
  line L1 C1 L2 C2 [i]    trace un trait entre deux points
  clear                   efface tout
  show                    affiche le dessin actuel
  predict                 demande au reseau de deviner le chiffre
  help                    affiche ces commandes
  quit                    quitte
"""


def new_grid() -> list[list[float]]:
    return [[0.0] * SIZE for _ in range(SIZE)]


def to_char(v: float) -> str:
    idx = min(int(v * len(RAMP)), len(RAMP) - 1)
    return RAMP[idx]


def render(grid: list[list[float]]) -> str:
    header = "     " + "".join(str(c % 10) for c in range(SIZE))
    lines = [header]
    for r, row in enumerate(grid):
        lines.append(f"{r:>3}  " + "".join(to_char(v) for v in row))
    return "\n".join(lines)


def set_pixel(grid: list[list[float]], r: int, c: int, intensity: float = 1.0) -> None:
    if 0 <= r < SIZE and 0 <= c < SIZE:
        grid[r][c] = max(grid[r][c], intensity)
        # soft neighbours: real MNIST strokes are a few pixels wide with
        # anti-aliased edges, not a single hard-edged pixel.
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                grid[nr][nc] = max(grid[nr][nc], intensity * 0.4)


def bresenham(r1: int, c1: int, r2: int, c2: int) -> list[tuple[int, int]]:
    points = []
    dr, dc = abs(r2 - r1), abs(c2 - c1)
    sr = 1 if r1 < r2 else -1
    sc = 1 if c1 < c2 else -1
    err = dr - dc
    r, c = r1, c1
    while True:
        points.append((r, c))
        if r == r2 and c == c2:
            break
        e2 = 2 * err
        if e2 > -dc:
            err -= dc
            r += sr
        if e2 < dr:
            err += dr
            c += sc
    return points


def draw_line(grid: list[list[float]], r1: int, c1: int, r2: int, c2: int, intensity: float = 1.0) -> None:
    for r, c in bresenham(r1, c1, r2, c2):
        set_pixel(grid, r, c, intensity)


def predict(network: Network, grid: list[list[float]]) -> tuple[list[int], list[float]]:
    flat = [v for row in grid for v in row]
    output = network.predict(Matrix([flat]))
    probs = output.data[0]
    ranked = sorted(range(10), key=lambda i: -probs[i])
    return ranked, probs


def run(network: Network, input_lines=None) -> None:
    """input_lines: optional list of commands, used by tests instead of
    interactive stdin."""
    grid = new_grid()
    source = iter(input_lines) if input_lines is not None else None

    while True:
        if source is not None:
            try:
                command = next(source)
            except StopIteration:
                break
        else:
            try:
                command = input("> ")
            except EOFError:
                break
        command = command.strip()
        if not command:
            continue
        parts = command.split()
        cmd = parts[0].lower()

        if cmd in ("quit", "exit"):
            break
        elif cmd == "help":
            print(HELP)
        elif cmd == "clear":
            grid = new_grid()
            print("Grille effacee.")
        elif cmd == "show":
            print(render(grid))
        elif cmd == "set" and len(parts) >= 3:
            r, c = int(parts[1]), int(parts[2])
            intensity = float(parts[3]) if len(parts) > 3 else 1.0
            set_pixel(grid, r, c, intensity)
            print(render(grid))
        elif cmd == "line" and len(parts) >= 5:
            r1, c1, r2, c2 = (int(p) for p in parts[1:5])
            intensity = float(parts[5]) if len(parts) > 5 else 1.0
            draw_line(grid, r1, c1, r2, c2, intensity)
            print(render(grid))
        elif cmd == "predict":
            ranked, probs = predict(network, grid)
            best = ranked[0]
            print(f"\n>>> Prediction : {best}  (confiance {probs[best]:.1%})")
            print("Classement complet :")
            for digit in ranked:
                bar = "#" * int(probs[digit] * 40)
                print(f"  {digit} : {probs[digit]:6.1%} {bar}")
        else:
            print("Commande inconnue. Tape 'help'.")


def main() -> None:
    model_path = sys.argv[1] if len(sys.argv) > 1 else "mnist_model.json"
    try:
        network = Network.load(model_path)
    except FileNotFoundError:
        print(f"Modele introuvable : {model_path}")
        print("Lance d'abord examples/mnist.py (ou mnist_improved.py) pour en creer un.")
        return

    print(f"Modele charge depuis {model_path}.")
    print(HELP)
    run(network)


if __name__ == "__main__":
    main()
