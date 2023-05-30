import os
import re
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

#Elenco dei server disponibili per il testing
servers = {"Atlanta" : "atl.speedtest.clouvider.net", "New York" : "nyc.speedtest.clouvider.net", "London" : "lon.speedtest.clouvider.net",
           "Los Angeles" : "la.speedtest.clouvider.net", "Paris" : "paris.testdebit.info", "Lille" : "lille.testdebit.info ",
           "Lyon" : "lyon.testdebit.info", "Aix-Marseille" : "aix-marseille.testdebit.info", "Bordeaux" : "bordeaux.testdebit.info "}

#Viene chiesto all'utente di inserire un server valido
server = input("Inserire il server al quale si vuole efettuare una sessione di ping: ").strip()
while server not in servers:
    print("Server " + server + " non disponibile\n")
    print("I server disponibili sono:")
    for key in servers.keys():
        print(key)
    print()
    server = input("Inserire il server al quale si vuole efettuare una sessione di ping: ").strip()

indirizzo = servers[server]

#Viene chiesto all'utente di inserire il numero di pacchetti da inviare. Se il numero è minore di 1 il programma termina.
c = int(input("Inserire il numero c di pacchetti da inviare per ogni sessione di ping per calcolare il ttl: "))
if c < 1:
    print("Devi inserire un numero maggiore di zero")
    exit(1)
print()

#Nel caso in cui nella directory sia già presente un file chiamato risultati_ping.txt, questo viene eliminato in modo tale da avere, alla fine del programma,
#un file con solo i dati raccolti dal testing
if Path("risultati_ping.txt").is_file():
    os.system("rm risultati_ping.txt")

#Pattern cercato tra le righe del file per capire quando il comando ping non riesce a far arrivare a destinazione i pacchetti inviati
pattern_line = re.compile(r"Time to live exceeded")
exceeded = False

#Ciclo per chiamare iterativamente il comando ping e stampare i dati nei due file txt
for t in range(50, 0, -1):
    print(f"Sto eseguendo il ping con -c {c} e -t {t} al server {indirizzo}\n")
    command = f"sudo ping -c {c} -t {t} -A {indirizzo}"
    
    #Scrivo il comando con i suoi specifici parametri nel file
    with open ("risultati_ping.txt", "a") as file:
        file.write(f"Ping con -c {c} e -t {t}\n\n")
        file.write(command + "\n")
    
    #I dati restituiti dal comando ping vengono salvati "temporaneamente" in risultati_temp.txt (tale file viene sovrascritto ad ogni iterazione del ciclo)
    #e allo stesso tempo salvati (in modalità append) nel file risultati_ping.txt
    os.system(command + " | tee risultati_temp.txt >> risultati_ping.txt")
    
    with open ("risultati_ping.txt", "a") as file:
        file.write("\n-----------------------------------------------------------------\n\n")
    
    #Cerco nel file "temporaneo" le righe con "Time to live exceeded" in modo tale da capire se interrompere il ciclo 
    with open ("risultati_temp.txt") as file:
        for line in file:
            if pattern_line.search(line) != None:
                exceeded = True
                break
    if exceeded:
        break

print(f"Utilizzando il metodo col comando ping, il numero di link attraversati è {t}")

#Chiamata al comando traceroute per verificare se il valore ottenuto prima è quello corretto
print(f"\nSto eseguendo il traceroute al server {indirizzo}\n")
command = "traceroute " + indirizzo
with open ("risultati_ping.txt", "a") as file:
        file.write(f"Traceroute all' indirizzo {indirizzo}\n\n")
os.system(command + " >> risultati_ping.txt")
with open ("risultati_ping.txt", "a") as file:
        file.write("\n-----------------------------------------------------------------\n\n")
same = False
with open ("risultati_ping.txt") as file:
    #Seleziono la penultima riga restituita dal comando, poichè l'ultima rappresenta il server stesso
    line = file.readlines()[-5] #-5 poichè sono state stampate, dopo il comando, una "riga separatrice" e due righe vuote (riga 78)
    #Cerco all'inizio della riga un pattern contenente eventuali spazi e almeno una cifra. Questo corrisponde al numero di link tra il client e il server
    match = re.match(r'^\s*(\d+)', line)
    if match:
        number = int(match.group(1))
        if number == t:
            same = True
if same:
    print(f"Utilizzando il metodo col comando traceroute, il numero di link attraversati è {t}, lo stesso ottenuto in precedenza")
else:
    print(f"Utilizzando il metodo col comando traceroute, il numero di link attraversati è {number}, diverso da quello ottenuto in precedenza")


Ls = range(20, 1472, 1000) #Range di inizio e arrivo della grandezza dei pacchetti inviati; step di 5 byte
c = 200 #Numero di pacchetti inviati ad ogni chiamata di ping

#Liste in cui salvo i valori restituiti da ogni chiamata a ping
mins = []
avgs = []
maxs = []
mdevs = []

#Ciclo per invocare il comando ping, salvare i dati sui file txt ed estrarli tramite l'uso delle regex
for L in Ls:
    print(f"\nSto eseguendo il ping con -c {c} -s {L} e -t infinito al server {indirizzo} per calcolare i vari RTT\n")
    command = f"sudo ping -c {c} -s {L} -A {indirizzo}"
    with open ("risultati_ping.txt", "a") as file:
        file.write(command + "\n")

    os.system(command + " | tee risultati_temp.txt >> risultati_ping.txt")

    with open ("risultati_ping.txt", "a") as file:
        file.write("\n\n")
    
    with open ("risultati_temp.txt") as file:
        #Dopo ogni esecuzione del comando cerco quella riga contente i dati relativi al RRT
        for line in file:
            match = re.search(r'(\d+[.]\d+)/(\d+[.]\d+)/(\d+[.]\d+)/(\d+[.]\d+)', line) #pattern suddiviso in 4 gruppi
            #Una volta trovata la riga, estraggo i dati e li aggiungo alle liste
            if match:
                mins.append(float(match.group(1)))  #minimo
                avgs.append(float(match.group(2)))  #media
                maxs.append(float(match.group(3)))  #massimo
                mdevs.append(float(match.group(4))) #dev standard


#Converto la dimensione da byte a bit per plottare i dati
Ls = [(L + 28) * 8 for L in Ls]

p = np.polyfit(Ls, mins, 1)
print(f"a = {p[0]}")
fit_line = [p[0] * L for L in Ls] + p[1]
s = t * 2 / p[0]
s_bottleneck = 2 / p[0]
print(f"S = {s}")
print(f"S_bottleneck = {s_bottleneck}")

with open("risultati_ping.txt", "a") as file:
    file.write(f"\n-----------------------------------------------------------------\n\nS = {s}\nS_bottleneck = {s_bottleneck}")

plt.scatter(Ls, mins, color = "red")
plt.plot(Ls, fit_line, linestyle = "dotted", color = "black", linewidth = 3)
plt.title("Andamento del valore minimo del RTT")
plt.xlabel("L (pkt size) - bits")
plt.ylabel("$RTT_{min(L)}$")
plt.grid()
plt.show()

plt.scatter(Ls, avgs, color = "blue")
plt.title("Andamento del valore medio del RTT")
plt.xlabel("L (pkt size) - bits")
plt.ylabel("$RTT_{avg(L)}$")
plt.grid()
plt.show()

plt.scatter(Ls, maxs, color = "purple")
plt.title("Andamento del valore massimo del RTT")
plt.xlabel("L (pkt size) - bits")
plt.ylabel("$RTT_{max(L)}$")
plt.grid()
plt.show()

plt.scatter(Ls, mdevs, color = "green")
plt.title("Andamento del valore della deviazione standard del RTT")
plt.xlabel("L (pkt size) - bits")
plt.ylabel("$RTT_{std(L)}$")
plt.grid()
plt.show()