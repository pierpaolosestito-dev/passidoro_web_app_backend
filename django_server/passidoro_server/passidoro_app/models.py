
from django.db import models

# Create your models here.
from rest_framework.permissions import IsAuthenticated


class TestingFile(models.Model):
    FileData = models.FileField(upload_to='images')

class Testing(models.Model):
    TestingID = models.AutoField(primary_key=True)
    TestingName = models.CharField(max_length=500)
    TestingSurname = models.CharField(max_length=500)

class Sezione(models.Model):
    Nome = models.CharField(primary_key=True,max_length=50)
    Email_Rappresentante = models.EmailField()

class ReportGiornaliero(models.Model):
    ID = models.AutoField(primary_key=True)
    Data = models.DateField()
    Pasto = models.CharField(max_length=25)
    Ha_dormito = models.BooleanField()
    Bisogni_fisiologici = models.CharField(max_length=250)
    Promemoria_genitori = models.CharField(max_length=500)
    Inviato = models.BooleanField()
    Modificato = models.BooleanField()




class Bambini(models.Model):

    ID = models.AutoField(primary_key=True)
    Nome = models.CharField(max_length=85)
    Cognome = models.CharField(max_length=30)
    Email_Genitore1 = models.EmailField(default=None, blank=True, null=True)
    Email_Genitore2 = models.EmailField(default=None, blank=True, null=True)
    Data_di_nascita = models.CharField(max_length=500)
    Orario_uscita = models.CharField(max_length=500)
    Avatar = models.CharField(max_length=500)
    NomeSezione = models.ForeignKey(Sezione,on_delete=models.CASCADE)
    IDReport = models.ForeignKey(ReportGiornaliero,on_delete=models.CASCADE)

class ResetPasswordCode(models.Model):
    ID = models.AutoField(primary_key=True)
    code_to_sent = models.IntegerField()

