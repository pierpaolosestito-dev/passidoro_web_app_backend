from dj_rest_auth.models import TokenModel
from django.contrib.auth.models import User
from rest_framework import serializers
from . import models

#To facilitate conversion in JSON format.

class TestingSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Testing
        fields = ("TestingID", "TestingName", "TestingSurname")

class SezioneSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Sezione
        fields = ("Nome", "Email_Rappresentante")

class TestingFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TestingFile
        fields = '_all_'
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'is_superuser'
        )
class TokenSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False,read_only=True)
    class Meta:
        model = TokenModel
        fields = ('key','user')
class ReportGiornalieroSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReportGiornaliero
        fields = ("ID","Data","Pasto","Ha_dormito","Bisogni_fisiologici","Promemoria_genitori","Inviato","Modificato")

class BambiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bambini
        fields = ("ID","Nome","Cognome","Email_Genitore1","Email_Genitore2","Data_di_nascita","Orario_uscita","Avatar","NomeSezione")

class BambinixReportSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("ID","Nome","Cognome","Inviato","Modificato")