import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monia_lib import outils_pratiques, neurone, memoire, vegetaux, chantiers, securite


class TestCalculatrice(unittest.TestCase):
    def test_operations_simples(self):
        self.assertEqual(outils_pratiques.calculer("2 + 3"), 5)
        self.assertEqual(outils_pratiques.calculer("10 / 4"), 2.5)
        self.assertEqual(outils_pratiques.calculer("2 ** 8"), 256)
        self.assertEqual(outils_pratiques.calculer("-5 + 2"), -3)

    def test_expression_invalide_leve(self):
        with self.assertRaises(Exception):
            outils_pratiques.calculer("__import__('os').system('echo hack')")


class TestCrypto(unittest.TestCase):
    def test_cesar_aller_retour(self):
        original = "Bonjour MonIA"
        chiffre = outils_pratiques.cesar(original, 5)
        self.assertEqual(outils_pratiques.cesar(chiffre, -5), original)

    def test_xor_reversible(self):
        donnees = outils_pratiques.xor_chiffrer("secret", "cle")
        dechiffre = bytes(b ^ "cle".encode()[i % 3] for i, b in enumerate(donnees))
        self.assertEqual(dechiffre.decode(), "secret")


class TestMotsDePasse(unittest.TestCase):
    def test_longueur_generee(self):
        mdp = outils_pratiques.generer_mot_de_passe(20)
        self.assertEqual(len(mdp), 20)

    def test_force_mot_de_passe_faible(self):
        niveau, score = outils_pratiques.evaluer_force("abc")
        self.assertLess(score, 3)

    def test_force_mot_de_passe_fort(self):
        niveau, score = outils_pratiques.evaluer_force("Tr3s!Solide#2024")
        self.assertGreaterEqual(score, 5)


class TestNeurone(unittest.TestCase):
    def test_neurone_apprend_and(self):
        n = neurone.Neurone(2)
        donnees = [([0, 0], 0), ([0, 1], 0), ([1, 0], 0), ([1, 1], 1)]
        for _ in range(1000):
            for entrees, cible in donnees:
                n.entrainer(entrees, cible, taux=0.5)
        self.assertLess(n.predire([0, 0]), 0.3)
        self.assertGreater(n.predire([1, 1]), 0.7)

    def test_reseau_xor_apprend(self):
        reseau, erreur_totale = neurone.entrainer_xor(epoques=6000)
        self.assertLess(erreur_totale, 0.6)
        for x, cible in neurone.DONNEES_XOR:
            _, sortie = reseau.avancer(x)
            self.assertEqual(round(sortie), cible)


class TestMemoire(unittest.TestCase):
    def setUp(self):
        self._original_data_dir = memoire.DATA_DIR
        self._tmp = tempfile.mkdtemp()
        memoire.DATA_DIR = self._tmp
        memoire.FICHIER_MEMOIRE = os.path.join(self._tmp, "memoire.json")

    def tearDown(self):
        memoire.DATA_DIR = self._original_data_dir
        memoire.FICHIER_MEMOIRE = os.path.join(self._original_data_dir, "memoire.json")
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_apprendre_et_retrouver(self):
        memoire.apprendre("Quelle est la capitale de la France ?", "Paris")
        self.assertEqual(memoire.chercher("Quelle est la capitale de la France ?"), "Paris")

    def test_recherche_approximative(self):
        memoire.apprendre("comment ca va", "Très bien, merci !")
        self.assertIsNotNone(memoire.chercher("comment ça va"))


class TestVegetauxEtDevis(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._original_fichier = vegetaux.FICHIER_VEGETAUX
        vegetaux.FICHIER_VEGETAUX = os.path.join(self._tmp, "vegetaux.json")
        vegetaux.DATA_DIR = self._tmp

    def tearDown(self):
        vegetaux.FICHIER_VEGETAUX = self._original_fichier
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_sauver_et_charger(self):
        vegetaux.sauver([{"nom": "Olivier", "type": "arbre", "exposition": "plein soleil"}])
        donnees = vegetaux.charger()
        self.assertEqual(len(donnees), 1)
        self.assertEqual(donnees[0]["nom"], "Olivier")

    def test_calcul_materiau_gravier(self):
        formule = chantiers.FORMULES_MATERIAUX["gravier (paillage, épaisseur 5cm)"]
        self.assertAlmostEqual(formule(20), 1.0)


class TestSecurite(unittest.TestCase):
    def test_detecte_eval(self):
        motifs_touches = [m for m, _ in securite.MOTIFS_VULNERABLES if __import__("re").search(m, "eval(entree_utilisateur)")]
        self.assertTrue(motifs_touches)

    def test_detecte_secret_code_en_dur(self):
        ligne = 'api_key = "abcd1234efgh"'
        motifs_touches = [m for m, _ in securite.MOTIFS_VULNERABLES if __import__("re").search(m, ligne)]
        self.assertTrue(motifs_touches)


if __name__ == "__main__":
    unittest.main()
