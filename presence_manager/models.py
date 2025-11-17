from django.db import models

# Create your models here.


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
    id_professeur = models.IntegerField()

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


class SeanceCoure(models.Model):
    """
    Représente une séance de cours spécifique, incluant la date, l'heure de début et de fin,
    et est liée à un horaire de cours via une clé étrangère.
    obtenu à partir de l'horaire de cours pour une date spécifique

    """

    horaire_cours = models.ForeignKey(HoraireCours, on_delete=models.CASCADE)
    date_seance = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()

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

    seance_coure = models.ForeignKey(SeanceCoure, on_delete=models.CASCADE)
    id_etudiant = models.IntegerField()
    present = models.BooleanField(default=False)

    def __str__(self):
        status = "Présent" if self.present else "Absent"
        return f"Étudiant {self.id_etudiant} - {status} pour la séance du {self.seance_coure.date_seance}"

    class Meta:
        db_table = "presence"
        verbose_name = "Présence"
        verbose_name_plural = "Présences"
