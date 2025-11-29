from rest_framework import serializers


class PresenceSubmitSerializer(serializers.Serializer):
    matricule = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    classe = serializers.CharField(required=True)
    cours = serializers.CharField(required=True)


from rest_framework import serializers
from .models import SeanceCours  # Assurez-vous que l'importation est correcte


class SeanceCoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeanceCours
        # On inclut tous les champs du modèle
        fields = [
            "id",
            "horaire_cours",
            "date_seance",
            "heure_debut",
            "heure_fin",
            "status",
        ]
        # Les champs en lecture seule sont utiles si vous utilisez ce serializer
        # pour la création/mise à jour et ne voulez pas que l'utilisateur modifie l'ID
        read_only_fields = ["id"]
