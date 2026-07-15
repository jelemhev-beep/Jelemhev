import math
import random


def sigmoid(x):
    x = max(-60, min(60, x))
    return 1 / (1 + math.exp(-x))


def sigmoid_derivee(y):
    return y * (1 - y)


class Neurone:
    def __init__(self, n_entrees):
        self.poids = [random.uniform(-1, 1) for _ in range(n_entrees)]
        self.biais = random.uniform(-1, 1)

    def predire(self, entrees):
        somme = sum(w * e for w, e in zip(self.poids, entrees)) + self.biais
        return sigmoid(somme)

    def entrainer(self, entrees, cible, taux=0.1):
        sortie = self.predire(entrees)
        erreur = cible - sortie
        gradient = erreur * sigmoid_derivee(sortie)
        for i in range(len(self.poids)):
            self.poids[i] += taux * gradient * entrees[i]
        self.biais += taux * gradient
        return erreur


def lecon_neurone():
    print("\n=== Leçon : le neurone ===")
    print("Un neurone artificiel fait trois choses très simples :")
    print("  1. Il reçoit des entrées (des nombres)")
    print("  2. Il les multiplie chacune par un 'poids', additionne, ajoute un biais")
    print("  3. Il passe le résultat dans une fonction d'activation (ici sigmoïde)\n")
    n = Neurone(2)
    entrees = [0.6, 0.9]
    somme = sum(w * e for w, e in zip(n.poids, entrees)) + n.biais
    sortie = n.predire(entrees)
    print(f"Exemple avec des poids aléatoires : {[round(w, 3) for w in n.poids]}, biais {round(n.biais, 3)}")
    print(f"Entrées : {entrees}")
    print(f"Somme pondérée : {round(somme, 3)}")
    print(f"Sortie (après sigmoïde) : {round(sortie, 3)}")
    print("\nUn seul neurone ne 'sait' rien au départ : ses poids sont réglés")
    print("au hasard. C'est l'entraînement (voir option 30) qui les ajuste.")


def lecon_apprendre_y_2x():
    print("\n=== Leçon : apprendre y = 2x ===")
    print("On va entraîner UN neurone tout simple à deviner y = 2x,")
    print("juste en lui montrant des exemples (x, y) et en corrigeant son erreur.\n")
    n = Neurone(1)
    n.poids = [random.uniform(-1, 1)]
    n.biais = 0.0
    exemples = [(x, 2 * x) for x in [0.1, 0.2, 0.3, 0.4, 0.5, -0.2, -0.4]]
    for epoque in range(2000):
        for x, y in exemples:
            sortie = sum(w * x for w in n.poids) + n.biais
            erreur = y - sortie
            n.poids[0] += 0.01 * erreur * x
            n.biais += 0.01 * erreur
        if epoque % 400 == 0:
            perte = sum((y - (n.poids[0] * x + n.biais)) ** 2 for x, y in exemples) / len(exemples)
            print(f"  époque {epoque:5d} : poids={n.poids[0]:.3f}  biais={n.biais:.3f}  erreur²={perte:.5f}")
    print(f"\nRésultat final : poids ≈ {n.poids[0]:.3f} (visé : 2.0), biais ≈ {n.biais:.3f} (visé : 0.0)")
    for x in [1, 3, -2]:
        print(f"  prédiction pour x={x} : {n.poids[0] * x + n.biais:.2f}  (vrai : {2*x})")


def lecon_entrainement():
    print("\n=== Leçon : s'entraîner ===")
    print("Entraîner un neurone = répéter une boucle :")
    print("  1. Prédire   2. Comparer à la vraie réponse (erreur)")
    print("  3. Ajuster un peu les poids dans le bon sens   4. Recommencer\n")
    print("Démo sur la fonction OR logique :")
    donnees = [([0, 0], 0), ([0, 1], 1), ([1, 0], 1), ([1, 1], 1)]
    n = Neurone(2)
    for epoque in range(500):
        erreur_totale = 0
        for entrees, cible in donnees:
            erreur_totale += abs(n.entrainer(entrees, cible, taux=0.3))
        if epoque % 100 == 0:
            print(f"  époque {epoque:4d} : erreur totale = {erreur_totale:.4f}")
    print("\nAprès entraînement :")
    for entrees, cible in donnees:
        print(f"  {entrees} → {n.predire(entrees):.3f}  (visé : {cible})")


class ReseauXOR:
    def __init__(self):
        self.w1 = [[random.uniform(-1, 1) for _ in range(2)] for _ in range(2)]
        self.b1 = [random.uniform(-1, 1) for _ in range(2)]
        self.w2 = [random.uniform(-1, 1) for _ in range(2)]
        self.b2 = random.uniform(-1, 1)

    def avancer(self, x):
        cache = [sigmoid(sum(self.w1[j][i] * x[i] for i in range(2)) + self.b1[j]) for j in range(2)]
        sortie = sigmoid(sum(self.w2[j] * cache[j] for j in range(2)) + self.b2)
        return cache, sortie

    def entrainer(self, x, cible, taux=0.5):
        cache, sortie = self.avancer(x)
        erreur_sortie = cible - sortie
        delta_sortie = erreur_sortie * sigmoid_derivee(sortie)
        deltas_cache = [delta_sortie * self.w2[j] * sigmoid_derivee(cache[j]) for j in range(2)]
        for j in range(2):
            self.w2[j] += taux * delta_sortie * cache[j]
        self.b2 += taux * delta_sortie
        for j in range(2):
            for i in range(2):
                self.w1[j][i] += taux * deltas_cache[j] * x[i]
            self.b1[j] += taux * deltas_cache[j]
        return erreur_sortie


DONNEES_XOR = [([0, 0], 0), ([0, 1], 1), ([1, 0], 1), ([1, 1], 0)]


def entrainer_xor(epoques=8000, taux=0.6, essais_max=10):
    """Un petit réseau à 2 neurones cachés peut rester bloqué dans un minimum
    local selon l'initialisation aléatoire : on relance si besoin."""
    for _ in range(essais_max):
        reseau = ReseauXOR()
        for _ in range(epoques):
            for x, cible in DONNEES_XOR:
                reseau.entrainer(x, cible, taux=taux)
        erreur_totale = sum(abs(cible - reseau.avancer(x)[1]) for x, cible in DONNEES_XOR)
        if erreur_totale < 0.5:
            return reseau, erreur_totale
    return reseau, erreur_totale


def lecon_reseau_xor():
    print("\n=== Leçon : le réseau (XOR) ===")
    print("XOR n'est pas résoluble par un seul neurone (les points ne sont pas")
    print("séparables par une ligne droite). Il faut une couche cachée : c'est")
    print("un petit réseau (2 entrées → 2 neurones cachés → 1 sortie).\n")
    print("(entraînement en cours, quelques essais peuvent être nécessaires...)")
    reseau, erreur_totale = entrainer_xor()
    print(f"  erreur totale finale : {erreur_totale:.4f}")
    print("\nAprès entraînement, le réseau a appris XOR :")
    for x, cible in DONNEES_XOR:
        _, sortie = reseau.avancer(x)
        print(f"  {x} → {sortie:.3f}  (visé : {cible})")
