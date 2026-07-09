# huntkit

Automatisation de reconnaissance et de detection de vulnerabilites pour le
bug bounty, a usage strictement personnel et legal : uniquement sur des
domaines que tu es explicitement autorise a tester (scope d'un programme de
bug bounty, ou tes propres domaines).

huntkit refuse de scanner tout domaine qui n'a pas ete ajoute explicitement
au scope. Il n'y a pas de contournement : c'est une garde-fou volontaire.

## Ce que ca fait

- **Enumeration de sous-domaines** : passive (logs Certificate Transparency
  via crt.sh) + brute-force DNS asynchrone sur une wordlist courante.
- **Scan de ports** : scanner TCP connect asynchrone sur les ports les plus
  courants, avec recuperation de banniere.
- **Checks de vulnerabilites**, architecture a plugins :
  - headers de securite manquants (CSP, HSTS, X-Frame-Options, ...)
  - chemins sensibles exposes (`.git/`, `.env`, credentials AWS, backups...)
  - certificats TLS expires ou auto-signes
- **Limiteur de debit** : concurrence et requetes/seconde plafonnees, pour
  rester dans les regles de la plupart des programmes de bug bounty.
- **Rapport Markdown** pret a coller dans une soumission.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Utilisation

```bash
# 1. Autoriser explicitement un domaine avant tout scan
python -m huntkit.cli scope add exemple-de-programme-bugbounty.com

# 2. Lancer la reconnaissance
python -m huntkit.cli recon exemple-de-programme-bugbounty.com

# 3. Generer le rapport
python -m huntkit.cli report exemple-de-programme-bugbounty.com
```

Options de `recon` : `--concurrency` (defaut 10) et `--rps` (requetes/seconde,
defaut 5) pour respecter la politique de debit du programme cible.

## Donnees

Stockees dans `~/.huntkit/huntkit.db` (SQLite). Change l'emplacement avec la
variable d'environnement `HUNTKIT_DATA_DIR`.

## Tests

```bash
pip install pytest
pytest
```

Tous les tests tournent en local (transport HTTP en memoire ou serveur de
test local) : aucun test ne fait de vraie requete vers un domaine externe.

## Avertissement

N'utilise cet outil que sur des cibles pour lesquelles tu as une autorisation
explicite (programme de bug bounty avec scope defini, tes propres systemes,
mandat client signe). Scanner des systemes sans autorisation est illegal dans
la plupart des juridictions.
