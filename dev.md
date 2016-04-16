
## Cos'è docker

![Logo docker](https://upload.wikimedia.org/wikipedia/commons/7/79/Docker_%28container_engine%29_logo.png)

## Storia di Docker

Docker nasce come tecnologia interna di un'azienda che vende PaaS, dotCloud. Ecco una breve cronologia:

- 2008: viene fondata dotCloud
- marzo 2013: prima versione open source, solo Ubuntu è supportata
- settembre 2013: annunciata partnership con Red Hat
- ottobre 2013: dotCloud fa pivot e diventa Docker, Inc.
- gennario 2014: round da 14M $
- settembre 2014: round da 40M $
- ottobre 2014: annunciata partnership con Microsoft (!)
- dicembre 2014: annunciata partnership con IBM
- aprile 2015: round da 95M $, si parla di valutazione miliardaria
- maggio 2015: principali contributor: Docker Inc., Red Hat, IBM, Google, Cisco Systems

## Cos'è docker

Docker è un sistema di:

- packaging di software e dipendenze (**image**)
- avvio di questi software in modo isolato rispetto al resto del sistema (**container**)

Inoltre docker è un **ecosistema** di tool per rendere super la gestione dei container.

Docker si avvale di alcune tecnologie del **kernel Linux**. Non si tratta di funzionalità disponibili solo su Linux, anzi! Su Solaris e *BSD esistono cose simili da molti anni, ma docker attualmente funziona solo su Linux e in ogni caso un'immagine creata per Linux non potrebbe girare su altri OS.

Nemmeno su Linux queste tecnologie sono veramente nuove: progetti come [OpenVZ](https://openvz.org/Main_Page) e [lxc](https://linuxcontainers.org/) sono in circolazione da anni, e queste funzionalità sono state inserite nel kernel da Google che già nel 2014 faceva girare tutto in container: [più di 2 miliardi di container avviati a settimana](http://www.theregister.co.uk/2014/05/23/google_containerization_two_billion/).

## Cos'è un container

Iniziamo da **cosa non è un container**. Nei primi tempi di docker, e probabilmente è l'approccio più naturale anche ora per chi inizia ad usarlo, docker veniva usato come se fosse una **macchina virtuale**:

- infilo in un container tutto quel che mi serve
- creo utenti
- espongo tutte le porte dei vari servizi

La verità è che se volete **veramente** fare questo lo strumento migliore è una **macchina virtuale**. Docker è scomodissimo per farlo.

![https://flic.kr/p/4A3YaZ](https://farm4.staticflickr.com/3105/2354410355_394d0eaa93_o_d.jpg)

Docker è un modo per:

- pacchettizzare software
- distribuirlo
- astrarre le particolarità del software così da poterlo avviare su un cluster in modo indipendente da quel che il software fa

Supponiamo di avere un'immagine ubuntu. Non "avvia ubuntu", quel che fa è:

- **avviare un processo** da un'immagine, ad esempio bash da ubuntu 16.04
- può fare **mount** di una directory della macchina host nel container
- può **mappare una porta** del container (es: 80) su una porta dell'host (es. 8000)

Il processo lanciato nel container "vede" il kernel dell'host ma le librerie dell'immagine utilizzata.

Questo è possibile grazie a 2 funzionalità del kernel Linux:

- namespace
- cgroup

I **namespace** sono sostanzialmente un sistema di isolazione. Quando un container viene avviato, docker crea dei namespace per lui, proibendo in questo modo ad altri container di andare ad interferire con la sua rete, i suoi processi (ogni container avrà un PID 1), etc. In questo modo quando un processo in un namespace/container fa fork, avvia un altro processo nel container!

I **cgroup** sono sistemi di limitazione e condivisione "fair" delle risorse, per fare in modo che nessun container si prenda tutta la CPU o la memoria del sistema.

### Demo

In questo training verrà usata l'immagine ufficiale python 3.5, basata su debian. Scarica l'immagine:

```
docker pull python:3.5-slim
```

Avvia una shell bash da questa immagine:

```
# docker run -it --rm python:3.5-slim bash
root@9632eb7cb0ae:/# ps aux
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  1.0  0.0  21948  3688 ?        Ss   20:30   0:00 bash
root         6  0.0  0.0  19188  2396 ?        R+   20:30   0:00 ps aux
```

come si può vedere la shell bash ha PID 1: process namespace. I flag qui usati sono `-i` e `-t` per lanciare il container in modalità interattiva, `--rm` per cancellare i dati del container quando il processo lanciato termina (uscita dalla bash in questo caso).

Avvia python:

```
# docker run -it --rm python:3.5-slim
```

### Esporre una porta

Posso ovviamente avviare un server http:

```
# docker run -it --rm python:3.5-slim python -m http.server
Serving HTTP on 0.0.0.0 port 8000 ...
```

Ma se provo ad accederci dall'host:

```
# curl localhost:8000
curl: (7) Failed to connect to localhost port 8000: Connessione rifiutata
```

Come mai? Network namespace! Esponiamo allora una porta tramite il flag `-p`:

```
# docker run -it --rm -p 9000:8000 python:3.5-slim python -m http.server
...
# curl localhost:9000
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
...
```

In questo modo ho esposto la porta 8000 del container sulla porta 9000 dell'host. Posso anche lasciare che sia docker a scegliere la porta per me, e vedere qual è la porta scelta:

```
# docker run -it --rm -p 8000 python:3.5-slim python -m http.server
...
# docker port (CONTAINER_ID|CONTAINER_NAME)
8000/tcp -> 0.0.0.0:32770
```

### Vedere quali container sono in esecuzione

Possiamo vedere quali container sono in esecuzione tramite:

```
# docker ps
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
c2f5bb98dab6        python:3.5-slim     "bash"              2 seconds ago       Up 2 seconds                            sleepy_brahmagupta
```

La prima colonna è il container ID, che corrisponde all'id del cgroup creato. L'ultima è un nome mnemonico assegnato casualmente da docker oppure impostabile tramite `docker run --name`.

### Volumi: persistenza dei dati

Il file system di un container è read-write, ma le scritture sono "effimere": non viene fatta persistenza sull'immagine, e quindi alla cancellazione del container vengono persi i file modificati durante la sua esecuzione. Per questo esistono i volumi. Qui vedremo i volumi "standard" di docker, locali alla macchina su cui vengono eseguiti i container.

Esistono 2 modi per montare un volume: su un path conosciuto dall'host oppure, come con le porte, possiamo lasciare che sia docker a decidere per noi.

Path "nascosto":

```
# docker run -it --rm -v /var/log python:3.5-slim bash
```

Path "scelto":

```
# docker run -it --rm -v /srv:/var/log python:3.5-slim bash
```

#### Volumi: pattern utili

- come visto sopra è comodo per esporre i log di un container
- utile se volete eseguire un DB con docker
- oltre che ad esporre/persistere i dati di un container, si può usare anche per "inserire" un file (sì, anche un file) o una directory in un container (pensate ad un container nginx in cui montate /etc/nginx/default.conf)

### Passaggio parametri tramite variabili d'ambiente

Un altro flag utile di `docker run` è quello per impostare variabili d'ambiente ad un container all'avvio:

```
# docker run -it --rm -e DB_HOST=db.example.com python:3.5-slim bash
root@4abd608fcd0d:/# echo $DB_HOST
db.example.com
```

Si tratta di un pattern molto diffuso perché le variabili d'ambiente vengono ereditate tra i processi, e quindi che io avvii direttamente python oppure una shell bash che compie delle inizializzazioni e poi fa `exec` di un processo python, a python stesso la variabile d'ambiente sarà raggiungibile indifferentemente.

### Riepilogo flag di `docker run`


| flag      | descrizione                                                     | esempio                     |
|:---------:|-----------------------------------------------------------------|-----------------------------|
| `-d`      | fai partire il container in background e mostra il container ID |                             |
| `-e`      | specifica una variabile d'ambiente                              | `-e DB_HOST=db.example.com` |
| `-it`     | fai partire il container in modalità interattiva                |                             |
| `--name`  | dai un nome mnemonico al container                              | `--name pg`                 |
| `--rm`    | cancella il container allo stop                                 |                             |
| `-p`      | esponi una porta                                                | `-p 8081:80`                |
| `-v`      | specifica un volume                                             | `-v /srv/pg-data:/pgdata`   |

### Altri comandi docker utili

```
docker stop (CONTAINER_ID|CONTAINER_NAME)
docker rm (CONTAINER_ID|CONTAINER_NAME)

# esegue command all'interno del container specificato
docker exec [-it] (CONTAINER_ID|CONTAINER_NAME) command

# vedi lo stdout del container, super utile!
docker logs [-f] (CONTAINER_ID|CONTAINER_NAME)

# risorse di uno o più container
docker stats (CONTAINER_ID|CONTAINER_NAME)
```

## Cos'è un'immagine

Un'immagine (image) è una **lista di layer** e di alcuni metadati.

Docker usa dei file system (**AUFS** è stato il primo) che implementano questa struttura a layer. Il funzionamento è semplice.

Prendiamo un file system definito dai layer [A, B]. Una **lettura** del file /home/vad/kitten.jpg eseguirà queste operazioni:

- è presente /home/vad/kitten.jpg nel layer A? Se sì, scegli quello, altrimenti:
- è presente /home/vad/kitten.jpg nel layer B? Se sì, scegli quello, altrimenti File not found.

Le **scritture** avverranno invece sempre nel layer più esterno, lasciando invariati quelli interni.

In AUFS in particolare un layer non è altro che una directory.

![AUFS layers](https://docs.docker.com/engine/userguide/storagedriver/images/aufs_layers.jpg)

È possibile allora costruire un'immagine basata su ubuntu semplicemente costruendo un'immagine composta da layer [A, ubuntu]. Il "layer" ubuntu si può recuperare tramite gli strumenti forniti da docker.

Per costruire un nostro layer ci sono un paio di modi:

- salvare lo stato di un container running (caso raro)
- scrivere e buildare un Dockerfile (molto comune)

### Dockerfile

Il `Dockerfile` è il file che contiene le istruzioni per creare un'immagine dal progetto corrente. Deve essere posto nella root del progetto o comunque in una directory padre di tutto quello che ci servirà nella build.

Andiamo a vedere come è fatto un Dockerfile

```Dockerfile
FROM python:3.5-slim

RUN pip install -q uwsgi==2.0.12

ADD ./requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

ADD ./docker/uwsgi.ini /etc/uwsgi.ini

ADD . /code

WORKDIR /code

EXPOSE 8080

CMD ["uwsgi", "--ini", "/etc/uwsgi.ini"]
```

Una precisazione: solitamente creare un'immagine personalizzata non vuol dire aggiungere un solo layer, ma un certo numero di layer. Per quale motivo? **Cache**! Prendiamo il Dockerfile di esempio: ogni riga genera un layer che potrà essere riutilizzato come cache fino a quando:

- quella riga non cambia
- non cambia un riga "sopra"
- non cambia una risorsa collegata (ad esempio nell'ADD di un file non cambia il file)

Vediamo ora come si fa la build di un'immagine:

```
# docker build -t pyconsette/demo .
Sending build context to Docker daemon 5.632 kB
Step 1 : FROM python:3.5-slim
 ---> b745b3281d66
Step 2 : ADD ./requirements.txt /requirements.txt
 ---> Using cache
 ---> 153d68df36ca
...
```

come si può vedere docker ci informa quando può utilizzare un layer già creato in precedenza. Altra informazione interessante è la prima riga di output: `Sending build context to Docker daemon 5.632 kB`. `docker build` impacchetta la directory corrente (quella che contiene il Dockerfile) e la usa per i comandi successivi. Ci informa di quanto sia grande questa directory. Se diventa troppo grande la build diventa lenta: meglio eliminare file o directory inutili tramite il file `.dockerignore`, in stile `.gitignore`.

### Dockerfile: come evitare il bloat

Abbiamo visto che ogni riga di un Dockerfile crea un nuovo layer. Questo vuol dire che ad esempio un Dockerfile fatto così:

```Dockerfile
...
RUN cd /src

RUN ./configure

RUN make

RUN make install

RUN cd /

RUN rm -rf /src
...
```

avrà un layer per ciascuno dei passi, e l'rm non servirà ad evitare che l'immagine contenga tutti gli oggetti creati dal compilatore in /src. Per questo l'unica soluzione è accorpare i passi:

```Dockerfile
...
RUN cd /src && \
   ./configure && \
   make && \
   make install && \
   cd / && \
   rm -rf /src
...
```

Un trucco simile si fa con apt:

```Dockerfile
RUN DEBIAN_FRONTEND=noninteractive apt-get update -qq && \
  apt-get install -qq -y python-dev && \
  apt-get clean -qq && \
  rm -rf /var/lib/apt/lists
```

Questa versione compatta ovviamente ha il problema di non usare la cache: è quindi preferibile non usarla durante lo sviluppo e passare a questa modalità solo una volta definiti tutti i passi.

## Docker registry: là dove vivono le images

Il primo comando usato in questo training è stato:

```
docker pull python:3.5-slim
```

Ma da dove arriva questa immagine? Niente di sorprendente per chi è abituato a registry come pypi, npm, apt: anche docker ha un registry pubblico: https://hub.docker.com.

Esistono immagini docker per quasi tutto:

- [python](https://hub.docker.com/_/python/)
- [ruby](https://hub.docker.com/_/ruby/)
- [java](https://hub.docker.com/_/java/)
- [ubuntu](https://hub.docker.com/_/ubuntu/)
- [debian](https://hub.docker.com/_/debian/)
- [alpine](https://hub.docker.com/_/alpine/)
- [postgreSQL](https://hub.docker.com/_/postgres/)
- redis, elasticsearch, jenkins

Tutte le immagini sopra sono ufficiali, ovvero supportate da docker e partner (le si riconosce per l'underscore nell'URL). Ma il docker hub è pubblico e gratuito, quindi anche voi potete pubblicare le vostre immagini. Si può anche collegare a **github** tramite hook per avere **build automatiche** ad ogni push.

Notare che stiamo usando l'immagine `python:3.5-slim`: `3.5-slim` è chiamato **tag** ed è usato per rappresentare sia versioni diverse di python che tipi di "immagini" diverse. Ad esempio `slim` qui indica che l'immagine base è più "magra" di quella di `python:3.5`: probabilmente si tratta di ubuntu vs debian. In questo momento tutte le immagini ufficiali stanno passando ad Alpine Linux per motivi di dimensione e sicurezza. Scelta discutibile...

## Registry privati

Quanto visto è molto utile per pubblicare immagini di software open source. Non tutti i software sono però adatti ad essere pubblicati. In questi casi è obbligatorio avere un registry privato. Esistono 3 possibilità:

- usare la **versione a pagamento di docker hub**
- usare registry di **terze parti**: ci sono startup che fanno questo per vivere! Oppure [AWS ECR](https://aws.amazon.com/it/ecr/)
- usare il [**registry open source**](https://github.com/docker/distribution) di docker, scritto in go e ovviamente disponibile come [immagine docker](https://hub.docker.com/_/registry/)

Noi abbiamo scelto di usare il registry open source installandolo in casa: funziona bene (almeno la versione 2, la corrente), è facile da installare, permette persistenza su file system locale o S3.

## Networking

Abbiamo già visto come esporre una porta, ma quella porta viene esposta sull'host. Come facciamo a fare in modo che un container si colleghi ad un altro container? Un container non può accedere all'host, almeno non in modo comodo (in pratica può, ma è un po' un hack). Per far comunicare i container esistono 2 modi:

- i link (legacy)
- le network (docker engine 1.9)

### Link

Docker supporta ormai da molte versioni i link tra container: permettono la comunicazione tra container in modo semplice.

Creo un container con nome e che espone una porta:

```
# docker run -it --rm --name http_server -p 8000 python:3.5-slim python -m http.server
Serving HTTP on 0.0.0.0 port 8000 ...
```

E posso interrogarlo da un altro container:

```
# docker run -it --rm --link http_server python:3.5-slim bash
root@7120837f7b71:/# set | grep HTTP_SERVER
HTTP_SERVER_ENV_GPG_KEY=97FC712E4C024BBEA48A61ED3A5CA953F73C700D
HTTP_SERVER_ENV_LANG=C.UTF-8
HTTP_SERVER_ENV_PYTHON_PIP_VERSION=7.1.2
HTTP_SERVER_ENV_PYTHON_VERSION=3.5.1
HTTP_SERVER_NAME=/elegant_ride/http_server
HTTP_SERVER_PORT=tcp://172.17.0.2:8000
HTTP_SERVER_PORT_8000_TCP=tcp://172.17.0.2:8000
HTTP_SERVER_PORT_8000_TCP_ADDR=172.17.0.2
HTTP_SERVER_PORT_8000_TCP_PORT=8000
HTTP_SERVER_PORT_8000_TCP_PROTO=tcp
root@7120837f7b71:/# python
Python 3.5.1 (default, Jan 26 2016, 05:51:15)
[GCC 4.9.2] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from urllib.request import urlopen
>>> urlopen('http://http_server:8000').read()
b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n<html>\n<head>\n<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n<title>Directory listing for /</title>\n</head>\n<body>\n<h1>Directory listing for /</h1>\n<hr>\n<ul>\n<li><a href=".dockerenv">.dockerenv</a></li>\n<li><a href=".dockerinit">.dockerinit</a></li>\n<li><a href="bin/">bin/</a></li>\n<li><a href="boot/">boot/</a></li>\n<li><a href="dev/">dev/</a></li>\n<li><a href="etc/">etc/</a></li>\n<li><a href="home/">home/</a></li>\n<li><a href="lib/">lib/</a></li>\n<li><a href="lib64/">lib64/</a></li>\n<li><a href="media/">media/</a></li>\n<li><a href="mnt/">mnt/</a></li>\n<li><a href="opt/">opt/</a></li>\n<li><a href="proc/">proc/</a></li>\n<li><a href="root/">root/</a></li>\n<li><a href="run/">run/</a></li>\n<li><a href="sbin/">sbin/</a></li>\n<li><a href="srv/">srv/</a></li>\n<li><a href="sys/">sys/</a></li>\n<li><a href="tmp/">tmp/</a></li>\n<li><a href="usr/">usr/</a></li>\n<li><a href="var/">var/</a></li>\n</ul>\n<hr>\n</body>\n</html>\n'
```

Si possono osservare 2 cose:

- vengono impostate alcune variabili d'ambiente che informano su IP e porte esposte dal container
- il server è raggiungibile tramite name del container usato come hostname! Figo!

Come avviene questo? Non sono un esperto di networking (anzi!), quel che so è che viene creata un'interfaccia di rete `docker0` e tramite regole iptables viene fatto routing tra i container:

```
# ifconfig
docker0   Link encap:Ethernet  IndirizzoHW 02:42:cf:7c:2f:88
          indirizzo inet:172.17.0.1  Bcast:0.0.0.0  Maschera:255.255.0.0
          indirizzo inet6: fe80::42:cfff:fe7c:2f88/64 Scope:Link
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:605 errors:0 dropped:0 overruns:0 frame:0
          TX packets:1173 errors:0 dropped:0 overruns:0 carrier:0
          collisioni:0 txqueuelen:0
          Byte RX:79915 (79.9 KB)  Byte TX:198070 (198.0 KB)
...
```

### Networks

Docker Engine 1.9 ha introdotto la creazione di network personalizzate. La funzionalità delle versioni precedenti è mantenuta tramite una network creata di default, chiamata `bridge0`. I container (a meno che non venga specificato diversamente) vengono lanciati in quella network.

Quali funzionalità aggiunge questa feature?

- possibilità di "isolare" container della stessa applicazione nella stessa network
- i link diventano opzionali: se sono nella stessa network possono comunicare come se fossero linkati
- ma soprattutto è stato aggiunto il supporto a network non locali! E i "tipi" di network sono pluggabili

Con Docker 1.9 è così possibile far comunicare container su macchine diverse come se fossero sulla stessa macchina, creando una "overlay network".

## Esercizio

Prendere il progetto fornito in `1-docker-engine` e:

- avviare un container postgreSQL
- creare un'immagine per il progetto
- avviare il progetto in un container


# Parte 2: docker-compose

[docker-compose](https://docs.docker.com/compose/) è nato da un azienda comprata da Docker, si chiamava `fig`. È sostanzialmente un modo per gestire un'applicazione formata da più container. Ah, è una figata :)

Nella nostra azienda lo usiamo per:

- definire tutte le **dipendenze** di un'applicazione e lanciarle durante lo sviluppo
- gestire la **build** su jenkins

## docker-compose per sviluppo

Si tratta del caso più semplice ma terribilmente utile. Supponiamo di star sviluppando un'applicazione basata su elasticsearch e redis. È facile definire un progetto compose in un file chiamato `docker-compose.yml`:

```yaml
elasticsearch:
  image: elasticsearch:1.7.5
  command: elasticsearch --node.local=true
  ports:
   - "127.0.0.1:9200:9200"

redis:
  image: docker.io/redis:2.8.21
  ports:
   - "127.0.0.1:6379:6379"
```

Per lanciare i due servizi mi basta quindi:

```
# docker-compose up -d
```

Per passare da un progetto ad un altro posso quindi semplicemente stoppare docker-compose con il comando `stop`, passare all'altro progetto e dare `up` nell'altro progetto. Non devo nemmeno ricordare quali siano le dipendenze di quel progetto. Fantastico.

Avere solo 2 dipendenze è spesso un sogno: immaginate in progetti complessi strutturati in microservice quanto sia utile.
