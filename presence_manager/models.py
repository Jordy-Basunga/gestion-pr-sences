from django.db import models
from uuid import uuid4
from presence_manager.utils import STATUT_CHOIX
from django.db import models
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, role=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, password, role="admin", **extra_fields)


class Utilisateur(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("student", "Student"),
        ("professor", "Professor"),
        ("section", "section"),
    )

    email = models.EmailField(unique=True, db_index=True)
    nom = models.CharField(max_length=150)
    postnom = models.CharField(max_length=150)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)

    # Permissions Django require these fields:
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # only email is required

    def __str__(self):
        return f"{self.email} ({self.role})"


class Professeur(models.Model):
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, related_name="professor_profile"
    )


class SectionAdmin(models.Model):
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, related_name="section_profile"
    )
    niveau_acces = models.CharField(max_length=100)

    class Meta:
        db_table = "section"
        verbose_name = "section"
        verbose_name_plural = "sections"


# Create your models here.
class Classe(models.Model):
    """
    Représente une classe (promotion) contenant un ensemble d'étudiants
    et associée à plusieurs cours.
    """

    nom = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    annee_academique = models.CharField(max_length=20, blank=True)  # ex : 2024-2025
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    code_terminal = models.UUIDField(
        default=uuid4, editable=False, unique=True, auto_created=True
    )

    def __str__(self):
        return self.nom

    class Meta:
        db_table = "classe"
        verbose_name = "Classe"
        verbose_name_plural = "Classes"


class Etudiant(models.Model):
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, related_name="student_profile"
    )
    matricule = models.CharField(max_length=20, unique=True, db_index=True)
    classe = models.ForeignKey(
        Classe,
        on_delete=models.SET_NULL,  # recommandation !
        null=True,
        related_name="etudiants",  # accès rapide : classe.etudiants.all()
    )


class Cours(models.Model):
    """
    Représente un cours avec ses détails tels que le nom, la description, le volume horaire, le statut,
    les timestamps de création et de mise à jour, et l'identifiant du professeur associé.
    elle permet de definir un cours qui aura des horaires specifiques
    """

    nom = models.CharField(max_length=100)
    description = models.TextField()
    volume_horaire = models.IntegerField()
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    classe = models.ForeignKey(
        Classe, on_delete=models.CASCADE, default=0, blank=True, null=True
    )
    professor = models.ForeignKey(
        Professeur, on_delete=models.CASCADE, null=True, related_name="courses"
    )

    def __str__(self):
        return self.nom

    class Meta:
        db_table = "cours"
        verbose_name = "Cours"
        verbose_name_plural = "Cours"


class HoraireCours(models.Model):
    """
    Représente l'horaire d'un cours spécifique, incluant le jour de la semaine et les heures de début et de fin.
    elle est liée à un cours via une clé étrangère.
    cest en partant de lui que la seance de presence sera cree par le cron du systeme
    """

    cours = models.ForeignKey(Cours, on_delete=models.CASCADE)
    jour_semaine = models.CharField(max_length=20)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()

    def __str__(self):
        return f"{self.cours.nom} - {self.jour_semaine} ({self.heure_debut} - {self.heure_fin})"

    class Meta:
        db_table = "horaire_cours"
        verbose_name = "Horaire de Cours"

        verbose_name_plural = "Horaires de Cours"


class SeanceCours(models.Model):
    """
    Représente une séance de cours spécifique, incluant la date, l'heure de début et de fin,
    et est liée à un horaire de cours via une clé étrangère.
    obtenu à partir de l'horaire de cours pour une date spécifique

    """

    horaire_cours = models.ForeignKey(HoraireCours, on_delete=models.CASCADE)
    date_seance = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    status = models.CharField(
        max_length=9,
        choices=STATUT_CHOIX,  # <- Application des choix ici
        default="en_cours",  # <- Optionnel : définir une valeur par défaut
        verbose_name="Statut",
    )

    def __str__(self):
        return f"Seance de {self.horaire_cours.cours.nom} le {self.date_seance}"

    class Meta:
        db_table = "seance_coure"
        verbose_name = "Séance de Cours"
        verbose_name_plural = "Séances de Cours"


class Presence(models.Model):
    """
    Représente la présence d'un étudiant à une séance de cours spécifique,
    incluant l'état de présence (présent ou absent) et est liée à une séance de cours via une clé étrangère.
    cette table represente Liste de presence des etudiants pour une seance donnee
    """

    seance_cours = models.ForeignKey(SeanceCours, on_delete=models.CASCADE)
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    present = models.BooleanField(default=False)

    def __str__(self):
        status = "Présent" if self.present else "Absent"
        return f"Étudiant {self.etudiant.id} - {status} pour la séance du {self.seance_cours.date_seance}"

    class Meta:
        db_table = "presence"
        verbose_name = "Présence"
        verbose_name_plural = "Présences"


import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta

from .models import Etudiant


class QRCode(models.Model):
    etudiant = models.ForeignKey(
        Etudiant, on_delete=models.SET_DEFAULT, default="ukw", related_name="qrcodes"
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)  # pour marquer s'il a été scanné/utilisé
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["expires_at"]),
        ]

    def save(self, *args, **kwargs):
        # Définir la date d'expiration par défaut si non fournie
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=365)  # par défaut 2h
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        """Vérifie si le QR code est encore valide."""
        return not self.used and timezone.now() < self.expires_at

    def mark_used(self):
        """Marque le QR comme utilisé."""
        self.used = True
        self.save()

    def __str__(self):
        return f"{self.etudiant.matricule} - QR {self.token} ({'valide' if self.is_valid else 'expiré'})"
