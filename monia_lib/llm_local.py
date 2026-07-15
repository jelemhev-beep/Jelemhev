import os

CHEMIN_MODELE_DEFAUT = "/root/modeles/qwen2.5-1.5b-instruct-q4_k_m.gguf"

_llm = None
_modele_charge_depuis = None


def chemin_modele():
    return os.environ.get("LLAMA_MODELE", CHEMIN_MODELE_DEFAUT)


def modele_disponible():
    return os.path.isfile(chemin_modele())


def _avertir_modele_manquant():
    print(f"⚠️  Modèle introuvable : {chemin_modele()}")
    print("   Télécharge un modèle .gguf (ex : Qwen2.5-0.5B-Instruct) et")
    print("   place-le à ce chemin, ou définis LLAMA_MODELE.")


def _charger():
    global _llm, _modele_charge_depuis
    chemin = chemin_modele()
    if _llm is not None and _modele_charge_depuis == chemin:
        return _llm
    try:
        from llama_cpp import Llama
    except ImportError:
        print("   ⚠️ Le paquet 'llama-cpp-python' n'est pas installé.")
        print("      Installe-le avec : pip install llama-cpp-python")
        return None
    if not modele_disponible():
        _avertir_modele_manquant()
        return None
    print("   ⏳ Chargement du modèle local (peut prendre un moment)...")
    try:
        _llm = Llama(model_path=chemin, n_ctx=2048, verbose=False)
        _modele_charge_depuis = chemin
        return _llm
    except Exception as e:
        print("   ⚠️ Échec du chargement du modèle :", e)
        return None


def generer(prompt, max_tokens=300):
    llm = _charger()
    if llm is None:
        return None
    try:
        sortie = llm.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return sortie["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("   ⚠️ Erreur pendant la génération :", e)
        return None


def llm_local():
    print("\n🧬 LLM local (Qwen2.5, gratuit, expérimental — setup requis)")
    if not modele_disponible():
        _avertir_modele_manquant()
        print("\n   Une fois le modèle en place, réessaie cette option.")
        return
    print(f"   Modèle détecté : {chemin_modele()}")
    print("   Pose une question ('q' pour revenir au menu)\n")
    while True:
        question = input("Toi (LLM local) : ").strip()
        if question.lower() in ("q", ""):
            break
        reponse = generer(question)
        if reponse:
            print(f"MonIA (local) : {reponse}\n")
        else:
            break
