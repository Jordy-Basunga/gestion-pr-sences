from rest_framework import serializers
from presence_manager.models import Classe, Utilisateur, Professeur, SectionAdmin, Etudiant
from django.db import transaction


from rest_framework import serializers
from django.db import transaction
from presence_manager.models import Utilisateur, Etudiant, Classe

class UtilisateurCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    matricule = serializers.CharField(required=False, max_length=100)
    classe_id = serializers.IntegerField(required=True)
    nom = serializers.CharField(required=True, max_length=150)
    postnom = serializers.CharField(required=True, max_length=150)
    role = serializers.ChoiceField(choices=Utilisateur.ROLE_CHOICES, required=True)
    password = serializers.CharField(
        write_only=True,
        min_length=6,
        style={"input_type": "password"}
    )

    class Meta:
        model = Utilisateur
        fields = [
            "email",
            "matricule",
            "classe_id",
            "nom",
            "postnom",
            "role",
            "password",
        ]

    def validate(self, attrs):
        # Validation rôle étudiant
        if attrs.get("role") == "student" and not attrs.get("matricule"):
            raise serializers.ValidationError({
                "matricule": "Le matricule est obligatoire pour les étudiants."
            })

        # Vérifier unicité email
        if Utilisateur.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError({
                "email": "Un utilisateur avec cet email existe déjà."
            })

        # Si classe_id fourni, vérifier qu'elle existe
        classe_id = attrs.get("classe_id")
        if classe_id is not None and not Classe.objects.filter(id=classe_id).exists():
            raise serializers.ValidationError({
                "classe_id": "Classe non existante."
            })

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        matricule = validated_data.pop("matricule", None)
        classe_id = validated_data.pop("classe_id", None)
        classe = None

        if classe_id:
            classe = Classe.objects.get(id=classe_id)

        # Création utilisateur et profil associé dans une transaction
        with transaction.atomic():
            user = Utilisateur(**validated_data)
            user.set_password(password)
            user.save()

           
            Etudiant.objects.create(utilisateur=user, matricule=matricule, classe=classe)
          

        return user
