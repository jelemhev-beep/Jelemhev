import sys

from . import devis, digits, llm_local, secondcerveau, voice

HELP = """
Commandes :
  chat [message]                    parle avec l'IA (Ollama local) ; reste en mode chat jusqu'a 'quit'/'0'/ligne vide
  parler                            comme 'chat' mais dicte au micro (Termux:API), reponses lues a voix haute
  projet <nom>                      change le projet actif (memoire separee par projet)
  note <titre>                      sauvegarde une note (contenu demande ensuite, ligne vide pour finir)
  notes [projet]                    liste les notes d'un projet (celui actif par defaut)
  recherche <terme>                 cherche dans tout le second cerveau
  devis <materiau> <surface> [ep]   calcule un devis (epaisseur en cm, 5 par defaut)
  materiaux                         liste les materiaux disponibles pour devis
  dessin [modele.json]              dessine un chiffre et demande au reseau neuralnet de le reconnaitre
  voix on|off                       active/desactive la sortie vocale (Termux:API)
  aide                              affiche ces commandes
  quitter                           quitte
"""

MENU = """
=== MonIA ===
  1) Discuter avec l'IA (Ollama local)
  2) Parler a l'IA au micro (dictee vocale)
  3) Changer de projet actif
  4) Prendre une note
  5) Voir mes notes
  6) Rechercher dans le second cerveau
  7) Calculer un devis
  8) Voir les materiaux disponibles
  9) Dessiner un chiffre (reconnaissance neuralnet)
  10) Activer/desactiver la voix
  0) Quitter

Tape un numero, ou une commande complete (ex: "chat bonjour"). 'aide' pour revoir tout ca.
"""

# words that end a chat/parler conversation loop and return to the main menu
_CHAT_EXIT_WORDS = ("quit", "quitter", "exit", "stop", "menu", "0")

# number -> (command, prompt). Commands needing no extra input aren't listed
# here; they're handled directly in _expand_menu_choice.
_PROMPTED_CHOICES = {
    "1": ("chat", "Ton message : "),
    "3": ("projet", "Nom du projet : "),
    "4": ("note", "Titre de la note : "),
    "6": ("recherche", "Terme a chercher : "),
    "7": ("devis", "Materiau, surface en m2, epaisseur en cm (optionnel) : "),
    "10": ("voix", "on ou off : "),
}
_DIRECT_CHOICES = {
    "0": "quitter",
    "2": "parler",
    "5": "notes",
    "8": "materiaux",
    "9": "dessin",
}


class Session:
    def __init__(self):
        self.project = "General"
        self.voice_enabled = False
        self.history: list[dict] = []


def _ensure_ollama_ready() -> bool:
    """Prints a clear message and returns False if Ollama isn't usable;
    tries to auto-start it first if it's installed but not running."""
    if llm_local.is_available():
        return True
    if not llm_local.is_installed():
        print(
            "Ollama n'est pas installe. Installe-le : "
            "curl -fsSL https://ollama.com/install.sh | sh "
            f"puis: ollama pull {llm_local.DEFAULT_MODEL}"
        )
        return False

    print("Ollama n'est pas demarre, tentative de demarrage automatique...")
    if llm_local.ensure_running():
        print("Ollama est pret.")
        return True

    print(
        "Echec du demarrage automatique. Lance-le toi-meme (`ollama serve &`) "
        f"et verifie que le modele est installe (`ollama pull {llm_local.DEFAULT_MODEL}`)."
    )
    return False


def _send_and_reply(session: Session, message: str) -> str | None:
    """Sends one user message to Ollama, keeping session.history and the
    second-brain conversation log in sync. Returns the reply, or None if
    the call failed (after printing the error and rolling back the
    pending history entry so a retry doesn't duplicate it)."""
    session.history.append({"role": "user", "content": message})
    secondcerveau.append_conversation(session.project, "user", message)

    try:
        reply = llm_local.chat(session.history)
    except llm_local.OllamaError as exc:
        print(f"Erreur: {exc}")
        session.history.pop()
        return None

    session.history.append({"role": "assistant", "content": reply})
    secondcerveau.append_conversation(session.project, "assistant", reply)
    return reply


def _expand_menu_choice(line: str, read_line) -> str:
    """Turns a bare menu number into the equivalent full command, prompting
    for any extra argument it needs. Anything that isn't a recognized menu
    number is returned unchanged (so raw commands keep working too)."""
    choice = line.strip().lower()

    if choice == "menu":
        print(MENU)
        return "aide"

    if choice in _DIRECT_CHOICES:
        return _DIRECT_CHOICES[choice]

    if choice in _PROMPTED_CHOICES:
        cmd, prompt = _PROMPTED_CHOICES[choice]
        print(prompt, end="")
        value = read_line().strip()
        return f"{cmd} {value}" if value else cmd

    return line


def handle_command(session: Session, line: str, source=None) -> bool:
    """Returns False when the session should end.

    `source`: None for real interactive stdin, or a shared iterator over
    upcoming commands (used by tests, and handed as-is to sub-loops like
    'note' and 'dessin' so they keep consuming from the same stream
    instead of a disconnected copy).
    """

    def read_line():
        if source is not None:
            return next(source)
        return input()

    parts = line.split(maxsplit=1)
    cmd = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""

    if cmd in ("quitter", "quit", "exit"):
        return False

    elif cmd in ("aide", "help"):
        print(MENU)
        print(HELP)

    elif cmd == "projet":
        if rest:
            session.project = rest
            session.history = []
        print(f"Projet actif : {session.project}")

    elif cmd == "chat":
        if not _ensure_ollama_ready():
            return True

        print("(mode chat : ligne vide, 'quit' ou '0' pour revenir au menu)")
        pending = rest
        while True:
            if pending:
                message = pending
                pending = ""
            else:
                print("Toi : ", end="")
                try:
                    message = read_line().strip()
                except (EOFError, StopIteration):
                    return False

            if not message or message.lower() in _CHAT_EXIT_WORDS:
                break

            reply = _send_and_reply(session, message)
            if reply is None:
                continue
            print(reply)
            if session.voice_enabled:
                voice.speak(reply)

    elif cmd == "parler":
        if not _ensure_ollama_ready():
            return True
        if not voice.is_stt_available():
            print("termux-speech-to-text introuvable (installe l'app Termux:API).")
            return True

        print("(mode vocal : parle, dis 'stop' pour revenir au menu)")
        while True:
            print("Ecoute...")
            message = voice.listen()
            if not message:
                print("(rien compris, reessaie ou dis 'stop')")
                continue

            print(f"Toi (voix) : {message}")
            if message.lower() in _CHAT_EXIT_WORDS:
                break

            reply = _send_and_reply(session, message)
            if reply is None:
                continue
            print(reply)
            voice.speak(reply)

    elif cmd == "note":
        title = rest or "note"
        print("Contenu (ligne vide pour terminer) :")
        lines = []
        while True:
            try:
                entry = read_line()
            except (EOFError, StopIteration):
                break
            if not entry:
                break
            lines.append(entry)
        path = secondcerveau.save_note(session.project, title, "\n".join(lines))
        print(f"Sauvegarde : {path}")

    elif cmd == "notes":
        target = rest or session.project
        notes = secondcerveau.list_notes(target)
        if not notes:
            print(f"Aucune note pour '{target}'.")
        for path in notes:
            print(f"  {path.name}")

    elif cmd == "recherche":
        if not rest:
            print("Usage: recherche <terme>")
            return True
        results = secondcerveau.search(rest)
        if not results:
            print("Aucun resultat.")
        for path, matching_line in results:
            print(f"  {path}: {matching_line}")

    elif cmd == "materiaux":
        print(", ".join(devis.available_materials()))

    elif cmd == "devis":
        args = rest.split()
        if len(args) < 2:
            print("Usage: devis <materiau> <surface_m2> [epaisseur_cm]")
            return True
        try:
            material = args[0]
            surface = float(args[1])
            thickness = float(args[2]) if len(args) > 2 else 5.0
            result = devis.calculate(material, surface, thickness)
        except ValueError as exc:
            print(f"Erreur: {exc}")
            return True
        text = devis.format_devis(result)
        print(text)
        secondcerveau.save_note(session.project, f"devis-{result.material}", text)

    elif cmd == "dessin":
        model_path = rest or None
        try:
            summary = digits.run_digit_session(model_path=model_path, input_lines=source)
        except digits.NeuralnetUnavailable as exc:
            print(f"Erreur: {exc}")
            return True
        if summary:
            path = secondcerveau.save_note(session.project, "dessin-chiffre", summary)
            print(f"(sauvegarde dans le second cerveau : {path})")

    elif cmd == "voix":
        if rest == "on":
            if voice.is_available():
                session.voice_enabled = True
                print("Voix activee.")
            else:
                print("termux-tts-speak introuvable (installe l'app Termux:API).")
        elif rest == "off":
            session.voice_enabled = False
            print("Voix desactivee.")
        else:
            print("Usage: voix on|off")

    else:
        print("Commande inconnue. Tape 'aide'.")

    return True


def run(input_lines=None) -> None:
    session = Session()
    source = iter(input_lines) if input_lines is not None else None

    def read_line():
        if source is not None:
            return next(source)
        return input()

    print("MonIA - assistant personnel")
    print(MENU)

    if llm_local.is_available():
        print("(Ollama deja disponible)")
    elif llm_local.is_installed():
        print("(Ollama installe mais pas lance, demarrage automatique au premier chat)")
    else:
        print("(Ollama n'est pas installe : 'chat'/'parler' resteront indisponibles)")

    while True:
        try:
            line = read_line().strip()
        except (EOFError, StopIteration):
            break
        if not line:
            continue
        line = _expand_menu_choice(line, read_line)
        if not handle_command(session, line, source):
            break


def main() -> None:
    run()


if __name__ == "__main__":
    sys.exit(main())
