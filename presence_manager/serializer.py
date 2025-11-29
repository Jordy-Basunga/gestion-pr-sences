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


from rest_framework import serializers
from .models import Utilisateur, Etudiant


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    matricule = serializers.CharField(
        required=False
    )  # obligatoire seulement si student
    classe_id = serializers.IntegerField(required=False)

    class Meta:
        model = Utilisateur
        fields = [
            "email",
            "nom",
            "postnom",
            "role",
            "password",
            "matricule",
            "classe_id",
        ]

    def validate(self, attrs):
        if attrs["role"] == "student" and "matricule" not in attrs:
            raise serializers.ValidationError(
                {"matricule": "Matricule obligatoire pour un étudiant"}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        matricule = validated_data.pop("matricule", None)
        classe_id = validated_data.pop("classe_id", None)

        # 1️⃣ création utilisateur
        user = Utilisateur(**validated_data)
        user.set_password(password)
        user.save()

        # 2️⃣ si étudiant → créer Etudiant
        if user.role == "student":
            Etudiant.objects.create(
                utilisateur=user, matricule=matricule, classe_id=classe_id
            )

        return user
