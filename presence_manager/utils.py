from django.test import TestCase

# Create your tests here.


def convertir_weekday_en_nom(weekday: int) -> str:
    """
    Convertit un entier de 0 à 6 en nom du jour en français.
    0 = Lundi, 1 = Mardi, ..., 6 = Dimanche
    """
    jours = {
        0: "Lundi",
        1: "Mardi",
        2: "Mercredi",
        3: "Jeudi",
        4: "Vendredi",
        5: "Samedi",
        6: "Dimanche",
    }
    return jours.get(weekday, "")


STATUT_CHOIX = [
    ("en_cours", "En Cours"),  # Stocké: 'en_cours', Affiché: 'En Cours'
    ("termine", "Terminé"),  # Stocké: 'termine', Affiché: 'Terminé'
    ("arrete", "Arrêté"),  # Stocké: 'arrete', Affiché: 'Arrêté')
]


def groupe_name(id_class) -> str:
    return f"classe_{id_class}"
