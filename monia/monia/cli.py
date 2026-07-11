import sys

from . import devis, digits, llm_cloud, llm_local, secondcerveau, voice

HELP = """
Commandes :
  chat <message>                    parle avec l'IA (Groq si une cle est configuree, sinon Ollama local)
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
  1) Discuter avec le LLM local
  2) Changer de projet actif
  3) Prendre une note
  4) Voir mes notes
  5) Rechercher dans le second cerveau
  6) Calculer un devis
  7) Voir les materiaux disponibles
  8) Dessiner un chiffre (reconnaissance neuralnet)
  9) Activer/desactiver la voix
  0) Quitter

Tape un numero, ou une commande complete (ex: "chat bonjour"). 'aide' pour revoir tout ca.
"""

# number -> (command, prompt). Commands needing no extra input aren't listed
# here; they're handled directly in _expand_menu_choice.
_PROMPTED_CHOICES = {
    "1": ("chat", "Ton message : "),
    "2": ("projet", "Nom du projet : "),
    "3": ("note", "Titre de la note : "),
    "5": ("recherche", "Terme a chercher : "),
    "6": ("devis", "Materiau, surface en m2, epaisseur en cm (optionnel) : "),
    "9": ("voix", "on ou off : "),
}
_DIRECT_CHOICES = {
    "0": "quitter",
    "4": "notes",
    "7": "materiaux",
    "8": "dessin",
}


class Session:
    def __init__(self):
        self.project = "General"
        self.voice_enabled = False
        self.history: list[dict] = []


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
        if not rest:
            print("Usage: chat <message>")
            return True

        session.history.append({"role": "user", "content": rest})
        secondcerveau.append_conversation(session.project, "user", rest)

        reply = None
        if llm_cloud.has_api_key():
            try:
                reply = llm_cloud.chat(session.history)
            except llm_cloud.GroqError as exc:
                print(f"Erreur Groq: {exc}")
                print("Repli sur le LLM local...")

        if reply is None:
            if not llm_local.is_available():
                print("Ollama non joignable, tentative de demarrage automatique...")
                if not llm_local.ensure_running():
                    print(
                        "Echec du demarrage automatique. Installe/lance Ollama toi-meme : "
                        "`ollama serve &` puis `ollama pull llama3.2`."
                    )
                    session.history.pop()
                    return True
                print("Ollama est pret.")
            try:
                reply = llm_local.chat(session.history)
            except llm_local.OllamaError as exc:
                print(f"Erreur: {exc}")
                session.history.pop()
                return True

        session.history.append({"role": "assistant", "content": reply})
        secondcerveau.append_conversation(session.project, "assistant", reply)
        print(reply)
        if session.voice_enabled:
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

    if llm_cloud.has_api_key():
        print("(Chat : Groq configure, pas besoin d'Ollama)")
    elif llm_local.is_available():
        print("(Ollama deja disponible)")
    elif llm_local.is_installed():
        print("(Ollama installe mais pas lance, demarrage automatique...)")
        if llm_local.ensure_running():
            print("Ollama est pret.")
        else:
            print("Echec du demarrage automatique. Tu pourras reessayer avec 'chat'.")
    else:
        print(
            "(Ollama n'est pas installe et aucune cle Groq configuree : "
            "'chat' restera indisponible)"
        )

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
