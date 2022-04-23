# Import InfluxDBClient library
from influxdb import InfluxDBClient
from random import randint
from random import randint
from statistics import mean
from time import sleep
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib



# influxdb settings
host = 'influx.biomed.ulb.ovh'
db = 'biomed3'  # replace by your database

# influxdb credentials
username = 'biomed3'  # replace by your database user login
password = 'Or1nqhDW5ynBvs4a'  # replace by your dabase user password

# init the influxdb client
client = InfluxDBClient(host=host, port=80, username=username, password=password, database=db)

# write data values 0 to 9 with a pause of 1 second between each in the measurment "testfor"
"""for i in range(2000):
    u= str(randint(30,50))
    y = str(randint(100,120))
    line1='testgrafana,id=testgrafana data={}'.format(u)
    line2='testgrafana,id=oxygen data1={}'.format(y)
    client.write_points(line1,protocol='line1') #write the line
    client.write_points(line2,protocol='line2') #write the line
    sleep(20)"""



fievre_mechant = 0.2  # Le pas entre 2 "étapes" de fièvre pour le monitoring de l'aggravation du symptôme.
nombre_mesures_minute_temp = 1  # Le nombre de mesures prises par le capteur de température pendant la minute de mesure.
nombre_mesures_heure_temp = 12  # Le nombre de mesures prises par le capteur de température en 1 heure.
pouls_mechant = 0.05  # Le pourcentage de différence entre les mesures de pouls pour que ça devienne inquiétant
                      # (/!\ c'est utilisé avec un produit, pas avec une somme)
nombre_mesures_minute_pouls = 1  # Le nombre de mesures prises par le capteur de pouls en 1 minute.
nombre_mesures_heure_pouls = 12  # Le nombre de mesures prises par le capteur de pouls en 1 heure.
nombre_mesures_journee_pouls = 12*24  # Le nombre de mesures prises par le capteur de pouls en 1 journée.

nombre_mesures_minute_o2 = 1  # Le nombre de mesures prises par le capteur de pouls en 1 minute.
nombre_mesures_heure_o2 = 12  # Le nombre de mesures prises par le capteur de pouls en 1 heure.
nombre_mesures_journee_o2 = 12*24  # Le nombre de mesures prises par le capteur de pouls en 1 journée.
patient = int(input("Si patient agée, malade, enfant ou femme enceinte mettre '1' , sinon mettre '0' "))



def envoie_mail(message):
    from_addr = 'biomed3ulb@gmail.com'
    to_addr = 'biomed3ulb@gmail.com'
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = ','.join(to_addr)
    msg['Subject'] = 'Informations suivi COVID-19'
    body = message
    msg.attach(MIMEText(body, 'plain'))
    email = "biomed3ulb@gmail.com"
    password = "azeqsd12"
    mail = smtplib.SMTP('smtp.gmail.com', 587)
    mail.ehlo()
    mail.starttls()
    mail.login(email, password)
    text = msg.as_string()
    mail.sendmail(from_addr, to_addr, text)
    mail.quit()


def clean_list_temp(values_list):
    """La fonction prend en entrée une liste de données de température (a priori provenant de la DB). Elle va en enlever
    les valeurs aberrantes et donner une liste de valeurs utilisables en sortie."""
    liste_propre = []
    for value in values_list:
        if value >= 30 and value <= 45:
            liste_propre.append(value)
    return liste_propre


def measure_temp(values_list):
    """La fonction prend en entrée une liste de données de température (a priori provenant de la DB). Elle va faire une
    moyenne des données récoltées pendant la dernière minute et peut donner deux valeurs différentes en sortie : la
    valeur de la température mesurée ou -1 s'il n'y avait que des données aberrantes, c'est-à-dire si le capteur a un
    problème ou qu'il n'était pas correctement porté."""
    valeurs_minute = clean_list_temp(values_list[-nombre_mesures_minute_temp:])
    if len(valeurs_minute) == 0:
        x = -1
    else:
        x = mean(valeurs_minute)
    return x


def monitoring_temp(values_list,iterateur=0):
    """La fonction prend en entrée une liste de données de température (a priori provenant de la DB). Elle va les
    analyser à l'aide d'autres fonctions et renvoyer la valeur de la température de l'utilisateur ainsi qu'un message
    lui décrivant l'état ainsi que l'évolution récente de sa fièvre."""

    valeur_temperature = measure_temp(values_list)
    c = iterateur
    if valeur_temperature == -1:
        z = "Veuillez vérifier le bon contact du capteur avec votre peau."
        w = 2
        if c == 2:
            envoie_mail(z)
            w = 0
    elif valeur_temperature > 40.5:
        return_value_instant = "Vous avez une fièvre sèvére"
        z = "Votre température est de " + str(valeur_temperature) + "°C. " + return_value_instant + " Pensez à contacter un médecin de manière urgente!."
        w = 3
        if c == 3:
            envoie_mail(z)
            w = 0

    else:
        if patient == 0:
            if valeur_temperature > 38:
                w = 4
                return_value_instant = "Vous avez de la fièvre"
                z = "Votre température est de " + str(valeur_temperature) + "°C. " + return_value_instant + " Pensez à contacter un médecin."
                if c == 4:
                    envoie_mail(z)
                    w= 0

            else:
                w = 0
                z = "Votre température est de " + str(valeur_temperature) + "°C, vous ne présentez pas de fièvre."
        elif patient == 1:
            if valeur_temperature > 37.2:
                w = 5
                return_value_instant = "Vous avez de la fièvre"
                z = "Votre température est de " + str(valeur_temperature) + "°C. " + return_value_instant + " Pensez à contacter un médecin."
                if w == 5 :
                    envoie_mail(z)
                    w = 0
            else:
                w = 0
                z = "Votre température est de " + str(valeur_temperature) + "°C, vous ne présentez pas de fièvre."

    return z,w


def clean_list_pulse(values_list):
    """La fonction prend en entrée une liste de données de fréquence cardiaque (a priori provenant de la DB). Elle va en enlever les
    valeurs aberrantes et donner une liste de valeurs utilisables en sortie."""
    liste_propre = []
    for value in values_list:
        if value >= 20 and value <= 150:
            liste_propre.append(value)
    return liste_propre


def measure_pulse(values_list):
    """La fonction prend en entrée une liste de données de fréquence cardiaque (a priori provenant de la DB). Elle va faire une
    moyenne des données récoltées pendant la dernière minute et peut donner deux valeurs différentes en sortie : la
    valeur d' fréquence cardiaque mesurée ou -1 s'il n'y avait que des données aberrantes, c'est-à-dire si le capteur a un
    problème ou qu'il n'était pas correctement porté."""
    valeurs_minute = clean_list_pulse(values_list[-nombre_mesures_minute_pouls:])
    if len(valeurs_minute) == 0:
        x = -1
    else:
        x = mean(valeurs_minute)
    return x


def measure_instability(values_list):
    """La fonction prend en entrée une liste de données de fréquence cardiaque (a priori provenant de la DB). Elle va comparer
    la moyenne des données récoltées sur la dernière minute et la moyenne des données récoltées sur la dernière heure.
    Elle peut donner 2 valeurs en sortie : 0 si la fréquence cardiaque est stable, 1 si la fréquence cardiaque varie."""
    valeurs_minutes = clean_list_pulse(values_list[-nombre_mesures_minute_pouls:])
    if len(values_list) == 0 or len(valeurs_minutes) == 0:
        return -1
    elif len(values_list) < nombre_mesures_heure_pouls:
        valeurs_heure = values_list
    else:
        valeurs_heure = values_list[-nombre_mesures_heure_pouls:]
    """valeurs_heure nécessite une réécriture. Si le capteur n'a pas été porté dans l'heure qui précède, les chiffres
        seront complètement biaisés. A voir comment sera écrite la fonction 'monitoring' finale, s'il y aura un bouton
        on/off et si on a le temps de le faire."""
    difference = mean(valeurs_minutes) - mean(valeurs_heure)
    if difference > fievre_mechant + 5 or difference < -5 - fievre_mechant:
        x = 0
    else:
        x = 1
    return x


def clean_list_o2(values_list):
    """La fonction prend en entrée une liste de données de Sp02 (a priori provenant de la DB). Elle va en enlever les
    valeurs aberrantes et donner une liste de valeurs utilisables en sortie."""
    liste_propre = []
    for value in values_list:
        if value > 100 and value <= 60:
            liste_propre.append(value)
    return liste_propre


def measure_o2(values_list):
    """La fonction prend en entrée une liste de données de Spo2 (a priori provenant de la DB). Elle va faire une
    moyenne des données récoltées pendant la dernière minute et peut donner deux valeurs différentes en sortie : la
    valeur d'Sp02 mesurée ou -1 s'il n'y avait que des données aberrantes, c'est-à-dire si le capteur a un
    problème ou qu'il n'était pas correctement porté."""
    valeurs_minute = clean_list_o2(values_list[-nombre_mesures_minute_o2:])
    if len(valeurs_minute) == 0:
        x = -1
    else:
        x = mean(valeurs_minute)
    return x


def monitoring_pulse(values_list,iterateur = 0):
    """La fonction prend en entrée une liste de données de fréquence cardiaque (a priori provenant de la DB). Elle va
    les analyser à l'aide d'autres fonctions et renvoyer la valeur de la fréquence cardiaque de l'utilisateur ainsi
    qu'un message lui décrivant l'état ainsi que l'évolution récente de sa situation."""
    return_value_instant = None
    valeur_pulse = measure_pulse(values_list)
    w = iterateur
    if valeur_pulse == -1:
        z = "Veuillez vérifier le bon contact du capteur avec votre peau."
        c = 2
        if w == 2:
            envoie_mail(z)
            c = 0
    elif valeur_pulse > 120 or valeur_pulse < 40:
        c = 3
        return_value_instant = "Votre fréquence cardiaque est très anormale !"
        z = "Votre fréquence cardiaque est de " + str(valeur_pulse) + "Bpm" + return_value_instant + " Pensez à contacter un médecin de manière urgente !!."
        if w == 3:
            envoie_mail(z)
            c = 0

    else:
        if patient == 0:
            if valeur_pulse > 100 or measure_instability(values_list) == 0:
                c = 4
                return_value_instant = "Votre fréquence cardiaque est élevée ou instable"
                z = "Votre fréquence cardiaque est de " + str(valeur_pulse) + "Bpm" + return_value_instant + " Pensez à contacter un médecin."
                if w == 4:
                    envoie_mail(z)
                    c = 0

            else:

                z = "Votre fréquence cardiaque est de " + str(valeur_pulse) + "Bpm, tout va bien."
                c=0
        elif patient == 1:
            if valeur_pulse > 95 or measure_instability(values_list) == 0:
                c = 5
                return_value_instant = "Votre fréquence cardiaque est élevée ou instable"
                z = "Votre fréquence cardiaque est de " + str(valeur_pulse) + "Bpm" + return_value_instant + " Pensez à contacter un médecin."
                if w == 5:
                    envoie_mail(z)
                    c = 0

            else:
                c = 0
                z = "Votre température est de " + str(valeur_pulse) + "°C, vous ne présentez pas de fièvre."

    return return_value_instant, z, c


def monitoring_o2(values_list,iterateur = 0 ):
    """La fonction prend en entrée une liste de données d'Spo2 (a priori provenant de la DB). Elle va les
    analyser à l'aide d'autres fonctions et renvoyer la valeur d'Spo2 de l'utilisateur ainsi qu'un message
    lui décrivant l'état ainsi que l'évolution récente de sa situation."""
    return_value_instant = None
    valeur_o2 = measure_o2(values_list)
    w = iterateur
    if valeur_o2 == -1:
        z="Veuillez vérifier le bon contact du capteur avec votre peau."
        c = 1
        if w == 1 :
            envoie_mail(z)
            c = 0

    elif valeur_o2 < 90:
        c = 2

        return_value_instant = "Votre taux d'Sp02 est trop bas!"
        z = "Votre taux d'Sp02 est de " + str(valeur_o2) + "%" + return_value_instant + " Pensez à contacter un médecin de manière urgente !!."
        if w == 2 :
            envoie_mail(z)
            c = 0

    else:
        if patient == 0 or patient == 1:
            if valeur_o2 <= 92 :
                c = 3
                return_value_instant = "Votre taux d'Sp02 est bas"
                z = "Votre taux d'Sp02 est de " + str(valeur_o2) + "%" + return_value_instant + " Pensez à contacter un médecin."
                if w == 3:
                    envoie_mail(z)
                    c = 0

            else:
                c = 0
                z = "Votre taux d'Sp02 est de " + str(valeur_o2) + "%, tout va bien."

    return return_value_instant, z,c

def traitement():
    alpha = 0
    beta = 0
    gamma = 0
    p = 1
    temp = []
    pulse = []
    o2 = []
    while p == 1 :

        query = 'SELECT temp FROM Experience2'  # testfor ou testgrafana
        results = client.query(query)
        points = list(results.get_points(measurement='Experience2'))
        temp.append(points[len(points)-1]["temp"])

        query1 = 'SELECT bpm FROM Experience2'  # testfor ou testgrafana
        results1 = client.query(query1)
        points1 = list(results1.get_points(measurement='Experience2'))
        pulse.append(points1[len(points1)-1]["bpm"])

        #query2 = 'SELECT o2 FROM o2_td'  # testfor ou testgrafana
        #results2 = client.query(query2)
        #points2 = list(results2.get_points(measurement='o2_td'))
        #o2.append(points2[len(points2)-1]["o2"])

        print(temp)
        print(pulse)
        #print(o2)


        x = monitoring_temp(temp,alpha)
        y = monitoring_pulse(pulse,beta)
        #z = monitoring_o2(o2,gamma)

        if x[1] == 2 :
            alpha = 2
        elif x[1] == 0 :
            alpha = 0
        elif x[1] == 3 :
            alpha = 3
        elif x[1] == 4 :
            alpha = 4
        elif x[1] == 5 :
            alpha = 5

        if y[2] == 2 :
            beta = 2
        elif y[2] == 3 :
            beta= 3
        elif y[2] == 0 :
            beta= 0
        elif y[2] == 4 :
            beta = 4
        elif y[2] == 5 :
            beta = 5
        sleep(300)
'''
        if z[2] == 2:
            gamma = 2
        elif z[2] == 3:
            gamma = 3
        elif z[2] == 0:
            gamma = 0
        elif z[2] == 4:
            gamma = 4
        elif z[2] == 5:
            gamma = 5
'''



traitement()
