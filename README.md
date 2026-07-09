# GitHome

Un hebergeur git minimaliste et prive, a heberger toi-meme. Comme un tout
petit GitHub perso : tu peux `git clone/push/pull` dessus en HTTP, et parcourir
tes depots (fichiers, commits, diffs) depuis une interface web.

Le vrai protocole git (smart HTTP) est delegue au binaire `git` lui-meme
(`git http-backend`), pour une compatibilite totale avec le client git. Le
reste (comptes, depots, navigation web) est ecrit ici.

## Demarrage

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Ouvre `http://localhost:8000`, cree ton compte via `/register` (le premier
compte seulement ; les suivants se creent avec `scripts/create_user.py`).

## Utiliser tes depots avec git

Depuis le dashboard, cree un depot. Tu obtiens une URL de clonage du type :

```
http://<host>:8000/<ton-nom>/<depot>.git
```

```bash
git clone http://<host>:8000/<ton-nom>/<depot>.git
cd <depot>
echo "hello" > README.md
git add README.md
git commit -m "premier commit"
git push
```

Git te demandera ton nom d'utilisateur/mot de passe (authentification HTTP
Basic). Pour eviter de les retaper a chaque fois, utilise un credential
helper git (`git config --global credential.helper store` ou `cache`).

## Recherche de code

Chaque `git push` reindexe automatiquement le depot concerne (index inverse
maison, scoring TF-IDF, en `app/search.py`). La barre de recherche en haut de
l'interface cherche dans tout ton code : identifiants entiers (`hash_token`)
et sous-mots (`hash`, `token` retrouvent aussi `hash_token`). Si un depot a ete
modifie autrement qu'avec un push HTTP (ex: manipulation directe des fichiers
bare), utilise le bouton "Reindexer tous mes depots" du dashboard.

## Donnees

Tout est stocke dans `./data/` (base SQLite + depots bare git), ignore par
git. Change l'emplacement avec la variable d'environnement
`GITHOME_DATA_DIR`.

## Tests

```bash
pip install pytest
pytest
```
