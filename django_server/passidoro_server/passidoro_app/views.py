import datetime
import os
import tempfile
from math import floor, ceil

from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.core import files
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import permission_classes, api_view
from rest_framework.exceptions import PermissionDenied, NotAuthenticated
from rest_framework.parsers import JSONParser
from django.http.response import JsonResponse, HttpResponse
from django.db import transaction, connection
from django.core.mail import send_mail, send_mass_mail, EmailMultiAlternatives,get_connection
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import exception_handler

from . import models,serializers
import json
from datetime import date
import secrets
import string

# Create your views here.
#from .models import SituazioneGiornaliera, SituazioneGiornalieraBambini, BambiniSezione
import requests

@csrf_exempt
def testing_file_api(request,namefile="",token=""):
    if request.method == "GET":
        try:
            if(Token.objects.get(key=token) == None):
                image_data = open("./images/default-avatar.jpg", "rb").read()
                return HttpResponse(image_data, content_type="image/jpeg")
            image_data = open("./images/"+namefile+".jpg", "rb").read()
            return HttpResponse(image_data,content_type="image/jpeg")
        except:
            image_data = open("./images/default-avatar.jpg", "rb").read()
            return HttpResponse(image_data, content_type="image/jpeg")


#Utility function
def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

@csrf_exempt
@api_view(['GET'])
def staff_api(request):
    if request.method == "GET":
        all_users = User.objects.filter(is_superuser=str2bool(request.headers['CUSTOM-OPTION'])).values()
        user_list = list(all_users)
        return JsonResponse(user_list, safe=False)

@csrf_exempt
@transaction.atomic
@api_view(['GET','POST','PUT','DELETE'])
def singolo_staff_api(request,id=0):
    if request.method == "GET":
                try:
                    user = User.objects.get(id=request.headers['CUSTOM-OPTION'])
                    serializer = serializers.UserSerializer(user)
                    return JsonResponse(serializer.data,safe=False)
                except:
                    return JsonResponse("Il profilo non esiste",safe=False)

    elif request.method == "PUT":
        staff_member_data = JSONParser().parse(request)
        staff_member = User.objects.get(id=staff_member_data['id'])
        serializer = serializers.UserSerializer(staff_member,data=staff_member_data,partial=True)
        if(serializer.is_valid()):
            serializer.save()
            return JsonResponse("OK",safe=False)
        else:
            return JsonResponse("ERRORE",safe=False)

    elif request.method == "POST":
         staff_member_data = JSONParser().parse(request)
         staff_member_name = staff_member_data['Nome']
         staff_member_surname = staff_member_data['Cognome']
         staff_member_email = staff_member_data['Email']
         staff_member_ruolo = staff_member_data['Ruolo']
         if(User.objects.filter(email=staff_member_email).exists()):
             return JsonResponse("Errore",safe=False)
         numbers = string.digits
         staff_member_username = staff_member_name.lower() + staff_member_surname.lower()+''.join(secrets.choice(numbers) for i in range(5))
         alphabet = string.ascii_letters
         password = ''.join(secrets.choice(alphabet) for i in range(8)).lower()

         html_message = render_to_string('nuovo_membro_staff_email.html', {"username": staff_member_username,"email_nuovo_membro":staff_member_email,"ruolo":staff_member_ruolo,"password":password})
         plain_message = strip_tags(html_message)
         from_email = "pierpaolo.sestito.1999@gmail.com"
         u=None
         if (send_mail("Iscrizione al sistema PASSI D'ORO", plain_message, from_email, [staff_member_email], html_message=html_message)) > 0:
             if staff_member_ruolo == "Maestra":
                 u =  User.objects.create_user(username=staff_member_username, email=staff_member_email, password=password,first_name=staff_member_name,last_name=staff_member_surname,)
             elif staff_member_ruolo == "Amministratore":
                 u = User.objects.create_superuser(username=staff_member_username, email=staff_member_email,password=password,first_name=staff_member_name,last_name=staff_member_surname,)

             return JsonResponse("OK",safe=False)
         return JsonResponse("Errore", safe=False)
    elif request.method == "DELETE":
        try:
            utente = User.objects.get(id=id)
            utente.delete()
            return JsonResponse("Utente eliminato con successo", safe=False)
        except:
            return JsonResponse("Utente non esistente", safe=False)

@csrf_exempt
@api_view(['GET','POST','PUT'])
def sezione_api(request):
    if request.method == "GET":
        try:
            sezione = models.Sezione.objects.all()
            sezione_serializer = serializers.SezioneSerializer(sezione,many=True)
            return JsonResponse(sezione_serializer.data,safe=False)
        except:
            return JsonResponse("Errore",safe=False)
    elif request.method == "PUT":
        try:
            sezione_request = JSONParser().parse(request)
            for row in sezione_request:
                sezione = models.Sezione.objects.get(Nome=row['Nome'])
                sezione_serializer = serializers.SezioneSerializer(sezione,data=row,partial=True)
                if sezione_serializer.is_valid():
                    sezione_serializer.save()
                else:
                    return JsonResponse("Errore",safe=False)
            return JsonResponse("OK",safe=False)
        except:
           return JsonResponse("La sezione non esiste",safe=False)
    elif request.method == "POST":
        sezione_data = JSONParser().parse(request)
        sezione_serializer = serializers.SezioneSerializer(data=sezione_data)
        if sezione_serializer.is_valid():
            sezione_serializer.save()
            return JsonResponse("Aggiunto con successo",safe=False)
        return JsonResponse("Inserimento non riuscito",safe=False)


@csrf_exempt
def recupero_cambio_password(request):
    if request.method == "POST":
        try:
            data = JSONParser().parse(request)
            code = models.ResetPasswordCode.objects.get(ID=data['id'])
            if(int(data["codice"]) != code.code_to_sent):
                return JsonResponse("Errore",safe=False)
            user = User.objects.get(email=data["Email"])
            passwordToCheck = data['Password']
            response = checkmatchesintoname(user.first_name,passwordToCheck)
            if(response == 1):
                return JsonResponse("La password è molto simile al tuo nome.",safe=False)

            responsesurname = checkmatchesintoname(user.last_name,passwordToCheck)

            if(responsesurname==1):
                return JsonResponse("La password è molto simile al tuo cognome",safe=False)

            user.set_password(passwordToCheck)
            user.save()

            code.delete()
            return JsonResponse("Password cambiata con successo",safe=False)
        except:
            return JsonResponse("Errore",safe=False)

#Utility function
def checkmatchesintoname(a,password):
    number = len(a)
    const_string = a
    meta_number = floor(len(const_string)/2)
    if(meta_number<=3):
        meta_number = ceil(len(const_string)/2)

    while(number>=meta_number):
        number -= 1
        if(a.lower() in password.lower() or a.upper() in password.upper()):
            return 1
        a = a.rstrip(a[-1])
    return -1
@csrf_exempt
def recupero_conferma_codice(request):
    if request.method == "POST":
        try:
            data = JSONParser().parse(request)
            security_code = models.ResetPasswordCode.objects.get(ID=data["id"])
            if(security_code.code_to_sent == int(data["codice"])):
                return JsonResponse("Codice corretto",safe=False)
            else:
                return JsonResponse("Codice errato",safe=False)
        except:
            return JsonResponse("Codice errato", safe=False)
@csrf_exempt
def recupero_password_api(request):
    if request.method == "POST":
        recupero_password_data = JSONParser().parse(request)
        if not User.objects.filter(email = recupero_password_data['Email']).exists():
            return JsonResponse("Risulta esserci un errore",safe=False)
        else:
            numbers = string.digits
            code_to_sent = ''.join(secrets.choice(numbers) for i in range(5))

            html_message = render_to_string('recupero_password_email.html',{"codice":code_to_sent})
            plain_message = strip_tags(html_message)
            from_email="pierpaolo.sestito.1999@gmail.com"
            if(send_mail("Recupero password",plain_message,from_email,[recupero_password_data['Email']],html_message=html_message))>0:
                recoverycode = models.ResetPasswordCode(code_to_sent=code_to_sent)
                recoverycode.save()
                object_to_return={"id":models.ResetPasswordCode.objects.last().ID}
                return JsonResponse(object_to_return,safe=False)
            else:
                return JsonResponse("Risulta esserci un errore",safe=False)


@csrf_exempt
@api_view(['POST'])
def invia_comunicazione_api(request):
    if request.method == "POST":
        try:
            email_data = JSONParser().parse(request)
            nome_sezione = email_data['Nome_sezione']
            oggetto = email_data['Oggetto']
            sezione_interessata = models.Sezione.objects.get(Nome=nome_sezione)

            html_message = render_to_string('comunicazione_email.html',{"oggetto":oggetto,"messaggio":email_data['Messaggio']})
            plain_message = strip_tags(html_message)
            from_email = "email_passidoro"
            to = []
            if email_data['Solo_rappresentante'] == "Si":
                to.append(sezione_interessata.Email_Rappresentante)
                if (send_mail(oggetto, plain_message, from_email, to,html_message=html_message )) > 0:
                    return JsonResponse("Email inviata con successo", safe=False)
                else:
                    return JsonResponse("Email non inviata", safe=False)
            else:
                bambini = models.Bambini.objects.filter(NomeSezione=nome_sezione)
                for i in bambini.iterator():
                    to.append(i.Email_Genitore1)
                    to.append(i.Email_Genitore2)
                if (send_mail(oggetto, plain_message, from_email, to, html_message=html_message)) > 0:
                    return JsonResponse("Email inviata con successo", safe=False)
                else:
                    return JsonResponse("Email non inviata", safe=False)
        except:
            return JsonResponse("Email non inviata", safe=False)
			
@csrf_exempt
@api_view(['POST'])
def invia_tutti_report_api(request):
    if request.method == "POST":
        with connection.cursor() as cursor:
            cursor.execute('SELECT passidoro_app_bambini.ID,passidoro_app_bambini.Nome,passidoro_app_bambini.Cognome,passidoro_app_bambini.Email_Genitore1,passidoro_app_bambini.Email_Genitore2,passidoro_app_bambini.IDReport_id FROM passidoro_app_bambini,passidoro_app_reportgiornaliero WHERE passidoro_app_bambini.IDReport_id = passidoro_app_reportgiornaliero.ID && passidoro_app_reportgiornaliero.Modificato = 1 && passidoro_app_reportgiornaliero.Inviato=0 && passidoro_app_bambini.NomeSezione_ID = %s',request.headers['CUSTOM-OPTION'])
            row = cursor.fetchall()
            if(len(row)==0):
                return JsonResponse("NO",safe=False)
            for child in row:
                report_giornaliero = models.ReportGiornaliero.objects.get(ID=child[5])
                to = []
                if(child[3]!=None):
                    to.append(child[3])
                if(child[4]!=None):
                    to.append(child[4])
                html_message = render_to_string('report_email.html',
                                                {"nome_completo_bambino": child[1] + " " + child[2],
                                                 "data": report_giornaliero.Data, "pasto": report_giornaliero.Pasto,
                                                 "dormito": 'SI' if report_giornaliero.Ha_dormito else 'NO',
                                                 "bisogni_fisiologici": report_giornaliero.Bisogni_fisiologici,
                                                 "promemoria": report_giornaliero.Promemoria_genitori})
                plain_message = strip_tags(html_message)
                numberOfEmailsSent = send_mail("Report giornaliero di " + child[1] + " " + child[2],
                                               plain_message,"babybot.passi.doro@gmail.com",recipient_list=to, html_message=html_message)
                if (numberOfEmailsSent > 0):
                    report_giornaliero.Inviato = True
                    report_giornaliero.save()
            return JsonResponse("OK",safe=False)
			
@csrf_exempt
@api_view(['POST'])
def invia_report(request):
    if request.method == "POST":
        data = JSONParser().parse(request)
        bambino = models.Bambini.objects.get(ID=data['ID'])
        report_giornaliero = models.ReportGiornaliero.objects.get(ID=bambino.IDReport.ID)

        html_message = render_to_string('report_email.html',
                                        {"nome_completo_bambino": bambino.Nome + " " + bambino.Cognome, "data": report_giornaliero.Data, "pasto":report_giornaliero.Pasto,"dormito":report_giornaliero.Ha_dormito,"bisogni_fisiologici":report_giornaliero.Bisogni_fisiologici,"promemoria":report_giornaliero.Promemoria_genitori})
        plain_message = strip_tags(html_message)
        from_email = 'pierpaolo.sestito.1999@gmail.com'
        to = []
        to.append(bambino.Email_Genitore1)
        to.append(bambino.Email_Genitore2)
        numberOfEmailsSent = send_mail("Report giornaliero di "+ bambino.Nome + " " + bambino.Cognome, plain_message, from_email, to, html_message=html_message)
        if (numberOfEmailsSent > 0):
            report_giornaliero.Inviato = True
            report_giornaliero.save()
            return JsonResponse("Email inviata con successo", safe=False)
        else:
            return JsonResponse("Email non inviata", safe=False)


@csrf_exempt
@api_view(['GET','PUT'])
def report_giornaliero_bambino_api(request):
    if request.method == "GET":
        try:
            if not models.Bambini.objects.filter(ID=request.headers['CUSTOM-OPTION']).exists():
                return JsonResponse("Il report non esiste",safe=False)
            bambino = models.Bambini.objects.get(ID=request.headers['CUSTOM-OPTION'])
            report_giornaliero = models.ReportGiornaliero.objects.filter(ID=bambino.IDReport.ID)
            report_giornaliero_serializer = serializers.ReportGiornalieroSerializer(report_giornaliero,many=True)
            return JsonResponse(report_giornaliero_serializer.data,safe=False)
        except:
            return JsonResponse("Il report non esiste",safe=False)

    elif request.method == "PUT":
        try:
            report_giornaliero_request = JSONParser().parse(request)
            bambino = models.Bambini.objects.get(ID=report_giornaliero_request['ID'])
            report_giornaliero = models.ReportGiornaliero.objects.get(ID=bambino.IDReport.ID)
            report_giornaliero_serializer = serializers.ReportGiornalieroSerializer(report_giornaliero, data=report_giornaliero_request,partial=True)
            if report_giornaliero_serializer.is_valid():
                report_giornaliero_serializer.save()
                return JsonResponse("Aggiornato con successo", safe=False)
            return JsonResponse("Aggiornamento non riuscito", safe=False)
        except:
            return JsonResponse("Aggiornamento non riuscito", safe=False)


@csrf_exempt
@api_view(['GET'])
def bambinixreport_sezione_api(request):
    if request.method == "GET":
        with connection.cursor() as cursor:
            cursor.execute('SELECT passidoro_app_bambini.ID,passidoro_app_bambini.Nome,passidoro_app_bambini.Cognome,passidoro_app_bambini.Avatar,passidoro_app_bambini.Orario_uscita,passidoro_app_reportgiornaliero.Inviato,passidoro_app_reportgiornaliero.Modificato FROM passidoro_app_bambini,passidoro_app_reportgiornaliero WHERE passidoro_app_bambini.IDReport_id = passidoro_app_reportgiornaliero.ID && passidoro_app_bambini.NomeSezione_ID = %s',request.headers['CUSTOM-OPTION'])
            row = cursor.fetchall()
            root = []
            for child in row:
                object = {"ID":child[0],"Nome":child[1],"Cognome":child[2],"Avatar":child[3],"Orario_uscita":child[4],"Inviato":child[5],"Modificato":child[6]}
                root.append(object)
            if(len(root) == 0):
                return JsonResponse("Non ci sono bambini",safe=False)
        return JsonResponse(root,safe=False)



@csrf_exempt
@transaction.atomic
@api_view(['GET','POST','DELETE'])
def bambini_api(request,sezione=""):
    if request.method == "GET":
        try:
            bambini = models.Bambini.objects.filter(NomeSezione=request.headers['CUSTOM-OPTION'])
            bambini_serializer = serializers.BambiniSerializer(bambini, many=True)
            return JsonResponse(bambini_serializer.data, safe=False)
        except:
            return JsonResponse("Non esistono bambini appartenenti a questa sezione",safe=False)
    elif request.method == "POST":
        data = JSONParser().parse(request)
        if (request.headers['CUSTOM-OPTION'] == "TUTTE"):
            bambini = models.Bambini.objects.all()
        else:
            bambini = models.Bambini.objects.filter(NomeSezione=request.headers['CUSTOM-OPTION'])
        today = datetime.date.today()
        for i in data:
            trovatoUguale = False
            for j in bambini:
                if (j.Nome == i['Nome'] and j.Cognome == i['Cognome'] and (
                        j.Email_Genitore1 == i['Email_Genitore1'] or j.Email_Genitore2 == i[
                    'Email_Genitore2']) and j.NomeSezione_id == i['NomeSezione'] and j.Data_di_nascita == i[
                    'Data_di_nascita']):
                    trovatoUguale = True
                    break
            if (not trovatoUguale):
                report_giornaliero_bambino = models.ReportGiornaliero(Data=today, Pasto="Non ancora selezionato",
                                                                      Ha_dormito=False,
                                                                      Bisogni_fisiologici="Non ancora inserito",
                                                                      Promemoria_genitori="Non ancora inserito",
                                                                      Inviato=False, Modificato=False)
                report_giornaliero_bambino.save()
                id_ultimo_report_inserito = models.ReportGiornaliero.objects.last()
                bambino = models.Bambini(Nome=i['Nome'], Cognome=i['Cognome'],
                                                                         Email_Genitore1=i['Email_Genitore1'],
                                                                          Email_Genitore2=i['Email_Genitore2'],
                                                                          Data_di_nascita=i['Data_di_nascita'],
                                                                          Orario_uscita="19:00", Avatar="default-avatar",
                                                                          NomeSezione=models.Sezione.objects.get(Nome=i['NomeSezione']),
                                                                          IDReport=id_ultimo_report_inserito)
                bambino.save()
            trovatoUguale = False

        return JsonResponse("OK", safe=False)

    elif request.method == "DELETE":
        try:
                bambini = models.Bambini.objects.filter(NomeSezione=sezione)
                for i in bambini.iterator():
                    i.IDReport.delete()
                bambini.delete()
                return JsonResponse("Bambini eliminati con successo",safe=False)
        except:
            return JsonResponse("Errore", safe=False)


@csrf_exempt
@transaction.atomic
@api_view(['GET','POST','PUT','DELETE'])
def singolo_bambino_api(request,id=0):
    if request.method == "GET":
        try:
                if not models.Bambini.objects.filter(ID=request.headers['CUSTOM-OPTION']).exists():
                    return JsonResponse("Il bambino non esiste")
                bambino = models.Bambini.objects.filter(ID=request.headers['CUSTOM-OPTION'])
                bambino_serializer = serializers.BambiniSerializer(bambino,many=True)
                return JsonResponse(bambino_serializer.data,safe = False)
        except:
            return JsonResponse("Il bambino non esiste",safe=False)


    elif request.method == "POST":
        bambino_data = JSONParser().parse(request)
        bambino_serializer = serializers.BambiniSerializer(data=bambino_data,partial=True)
        if bambino_serializer.is_valid():
            today = datetime.date.today()
            report_giornaliero_bambino = models.ReportGiornaliero(Data=today,
                                                                  Pasto="Non ancora selezionato", Ha_dormito=False,
                                                                  Bisogni_fisiologici="Non ancora inserito",
                                                                  Promemoria_genitori="Non ancora inserito",
                                                                  Inviato=False, Modificato=False)
            report_giornaliero_bambino.save()
            id_ultimo_report_inserito = models.ReportGiornaliero.objects.last()

            if(bambino_data['Avatar']!="default-avatar"):

                today = datetime.date.today()
                response = requests.get(bambino_data['Avatar'], stream=True)
                filename = bambino_data['Avatar'].split('/')[-1]
                filename = filename.split('.')[0]
                filename = filename + bambino_data['Nome']+bambino_data['Cognome']+bambino_data['Data_di_nascita']+str(today)+".jpg"
                lf = tempfile.NamedTemporaryFile()

                for block in response.iter_content(1024 * 8):
                    if not block:
                        break
                    lf.write(block)
                image = models.TestingFile()
                bambino_data['Avatar'] = filename.split('.')[0]
                image.FileData.save(filename, files.File(lf))
            bambino = models.Bambini(Nome = bambino_data['Nome'],Cognome = bambino_data['Cognome'], Email_Genitore1 = bambino_data['Email_Genitore1'],Email_Genitore2 = bambino_data['Email_Genitore2'], Data_di_nascita = bambino_data['Data_di_nascita'],Orario_uscita = bambino_data['Orario_uscita'],Avatar = bambino_data['Avatar'],NomeSezione = models.Sezione.objects.get(Nome = bambino_data['NomeSezione']),IDReport = id_ultimo_report_inserito)
            bambino.save()
            return JsonResponse("Aggiunto con successo", safe=False)
        return JsonResponse("Bambino non aggiunto", safe=False)

    elif request.method == "PUT":
        try:
            bambino_request = JSONParser().parse(request)
            bambino = models.Bambini.objects.get(ID=bambino_request['ID'])
            avatarPrePut = bambino.Avatar
            bambino_serializer = serializers.BambiniSerializer(bambino, data=bambino_request,partial=True)
            if bambino_serializer.is_valid():
                bambino_serializer.save()
                if("Avatar" in bambino_request):
                    if(avatarPrePut != "default-avatar"):
                        os.remove("./images/" + avatarPrePut + ".jpg")
                    numbers = string.digits
                    today = datetime.date.today()
                    response = requests.get(bambino_request['Avatar'], stream=True)
                    filename = bambino_request['Avatar'].split('/')[-1]
                    filename = filename.split('.')[0]
                    filename = filename + str(bambino_request['ID'])+str(today)+''.join(secrets.choice(numbers) for i in range(5))+".jpg"
                    lf = tempfile.NamedTemporaryFile()
                    for block in response.iter_content(1024 * 8):
                        if not block:
                            break
                        lf.write(block)
                    image = models.TestingFile()
                    bambino.Avatar = filename.split('.')[0]
                    bambino.save()
                    image.FileData.save(filename, files.File(lf))
                return JsonResponse("Aggiornato con successo", safe=False)
            return JsonResponse("Aggiornamento non riuscito", safe=False)
        except:
            return JsonResponse("Aggiornamento non riuscito",safe=False)

    elif request.method == "DELETE":
        try:
                bambino = models.Bambini.objects.get(ID=id)
                if(bambino.Avatar != "default-avatar"):
                    os.remove("./images/" + bambino.Avatar + ".jpg")
                bambino.IDReport.delete()
                bambino.delete()
                return JsonResponse("Bambino eliminato con successo",safe=False)
        except:
            return JsonResponse("Il bambino non esiste",safe=False)


@csrf_exempt
@api_view(['POST'])
def verifypassword(request):
    if request.method=="POST":
        try:
            data = JSONParser().parse(request)
            token = Token.objects.get(key=request.headers['Authorization'].split()[1])
            user = User.objects.get(id=token.user_id)
            if (check_password(data['password'], user.password)):
                return JsonResponse("Password verificata",safe=False)
            else:
                return JsonResponse("Password errata",safe=False)
        except:
            return JsonResponse("Errore",safe=False)

 #
 #        _                             _                     _   _ _                 _
 #       (_)                           | |                   | | (_) |               | |
 #  _ __  _  ___ _ __ _ __   __ _  ___ | | ___  ___  ___  ___| |_ _| |_ ___ ______ __| | _____   __
 # | '_ \| |/ _ \ '__| '_ \ / _` |/ _ \| |/ _ \/ __|/ _ \/ __| __| | __/ _ \______/ _` |/ _ \ \ / /
 # | |_) | |  __/ |  | |_) | (_| | (_) | | (_) \__ \  __/\__ \ |_| | || (_) |    | (_| |  __/\ V /
 # | .__/|_|\___|_|  | .__/ \__,_|\___/|_|\___/|___/\___||___/\__|_|\__\___/      \__,_|\___| \_/
 # | |               | |
 # |_|               |_|