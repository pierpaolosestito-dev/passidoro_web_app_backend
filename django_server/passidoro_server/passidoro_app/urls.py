from django.urls import include, re_path, path
from . import views

urlpatterns=[





    #re_path('^login$', views.login2),
    #re_path('^logout$', views.logout2),
    #re_path('^testingfile/(.+)$',views.testing_file_api),
    re_path('^testingfile/(.+)/(.+)$',views.testing_file_api),
    path('auth/',include('dj_rest_auth.urls')),

   #primo:user_id, secondo:idperladelete

    re_path('^sezione$',views.sezione_api),
    re_path('^sezione/([a-z]+)$',views.sezione_api),

    re_path('^singolo_bambino$',views.singolo_bambino_api),
    re_path('^singolo_bambino/([0-9]+)$',views.singolo_bambino_api),

    re_path('^verifica_password$',views.verifypassword),

    re_path('^bambini$',views.bambini_api),
    re_path('^bambini/([a-z]+)$',views.bambini_api),

    re_path('^bambinixreportsezione$',views.bambinixreport_sezione_api),

    re_path('^report_giornaliero$', views.report_giornaliero_bambino_api),
    re_path('^report_giornaliero/([0-9]+)$',views.report_giornaliero_bambino_api),

    re_path('^staff$',views.staff_api),
    re_path('^singolo_staff$', views.singolo_staff_api),
    re_path('^singolo_staff/([0-9]+)$',views.singolo_staff_api),

    re_path('^recupero_password$', views.recupero_password_api),
    re_path('^recupero_password/cambio_password$', views.recupero_cambio_password),
    re_path('^recupero_password/conferma_codice$', views.recupero_conferma_codice),
    re_path('^invia_comunicazione$', views.invia_comunicazione_api),
    re_path('^invia_report$',views.invia_report)

]