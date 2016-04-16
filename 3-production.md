
# Ecosistema docker

Abbiamo già visto 2 dei 4 strumenti creati da Docker (l'azienda). I 4 strumenti sono:

- Docker Engine
- Docker Compose
- Docker Machine
- Docker Swarm

Di docker machine non parlerò, ma potete facilmente trovare documentazione online.

## Quale problema risolvono i tool come Swarm?

Arriviamo alla messa in produzione. Avete alcune macchine, fisiche o virtuali. Avete i container. Come li lanciate? Vorremmo uno strumento che ci permetta di:

- **astrarci dalle macchine fisiche**: non preoccuparci di dove viene lanciato il container
- poter **accedere** all'applicazione indipendentemente da dove stia girando il container
- **scalare** l'applicazione orizzontalmente
- avere high-availability tramite **re-scheduling** del container in caso di node failure
- fare **rolling update**: rilasciare gradualmente i container con la nuova app, controllare che funzionino, e spegnere gradualmente i vecchi container

Esistono alcuni strumenti che fanno questo:

- **Docker Swarm**: creato dal team di Docker, è il più recente e quindi immaturo. Promettente ma non adatto a production
- **Amazon ECS**: se si usa AWS è pronto all'uso e gratis. Usabile in production ma con molti problemi
- **Kubernetes**: il re del settore, frutto di 10 anni di esperienza di Google. Setup complicato, molta visibilità su quel che succede

## Docker Swarm

Swarm trasforma un insieme di host docker in **un unico host docker virtuale**. Swarm infatti "parla" il **protocollo docker** standard, rendendolo così compatibile con strumenti di base come `docker` CLI ma anche con docker-compose oppure Jenkins tramite i suoi plugin.

Questa è sia la sua forza che la sua debolezza. Punto di forza ad esempio proprio l'integrazione con docker-compose, che permette di lanciare famiglie di container dipendenti tra loro (pensate ad un servizio python + container nginx come reverse proxy) descrivendole in un formato conosciuto, utilizzabile come visto dallo sviluppo alla build e portandolo così anche in produzione.

Altro punto di forza il poter usare comandi "standard" come `docker logs` per ispezionare un qualunque container nel cluster.

Debolezza perché questa compabilità a volte risulta forzata. Ed esempio per specificare regole di scheduling custom come ad esempio "avvia questo container solo su macchine con dischi SSD" vengono usate variabili d'ambiente invece di avere una sintassi rigida nella configurazione. Questo è solo un esempio banale di problemi più complicati che questa forzata compatibilità si porta dietro.

Al momento uno dei problemi maggiori, penso anch'esso dovuto alla compatibilità, è che non è previsto un meccanismo per fare rolling update. Così come con docker, i container si avviano e stoppano. E basta.

## Amazon ECS

[ECS](http://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html) ha un grande vantaggio: se si usano AWS ed EC2 per usarlo basta avviare sui propri nodi un container con l'agent ECS che:

- comunica con le API ECS
- viene comandato dalle API ECS
- avvia container
- termina container
- informa ECS di eventuali container che sono "usciti"/stati terminati
- invia metriche a CloudWatch

![Architettura ECS](http://docs.aws.amazon.com/AmazonECS/latest/developerguide/images/load-balancing.png)

Funzionalità:

- definizione di gruppi di container (family), *à la* docker compose ma con formato diverso
- avvio di family one-shot per comandi (ad esempio per migrare il DB)
- avvio di family long-running e rescheduling in caso di fallimento
- monitoraggio salute dei container tramite [Amazon ELB](https://aws.amazon.com/it/elasticloadbalancing/)

Ha però dei lati negativi:

- mancanza di **tools**
- mancata integrazione con **CloudWatch Logs**
- l'agent ha spesso problemi di memory leaks, oppure lascia container running
- ECS non si accorge di **nodi falliti** perché muore anche l'agent e quindi non fa rescheduling dei container
- **sviluppo lento**
- per lo scheduling richiede di impostare **limiti di memoria**, e... questo potrebbe portare a qualche "problemino" con l'oom-killer

![OOM Killer](https://raw.githubusercontent.com/vad/pycon7-docker-training/master/_images/oom-killer.png)

## Kubernetes

Kubernetes è, secondo Google, lo strumento nato dai suoi 10 anni di esperienza nel settore. Non è solo uno strumento per eseguire container docker, è un **SO per cluster**.

Kubernetes viene offerto **as a service** sul cloud di Google, rendendolo scelta ovvia in quel caso.

L'utilizzo in **AWS** è invece più complicato: Kubernetes usa pesantemente SDN (software defined networks) per cui è molto complicato configurarlo a mano. Viene fornito uno script per la configurazione di una VPC e creazione di un autoscaling group, ma si tratta una black box e bisogna capire come integrare con l'infrastruttura esistente.

L'alternativa, valida anche su cluster **bare metal** è usare un sofware di SDN come [flannel](https://coreos.com/flannel/docs/latest/), con però notevole perdita di prestazioni.

### Architettura

![Architettura Kubernetes](https://github.com/kubernetes/kubernetes/raw/master/docs/design/architecture.png?raw=true)

### Avvio di Kubernetes locale

Iniziamo avviando una versione locale di Kubernetes, single node. Prima di farlo verificate di **non avere container running**, evitando così problemi di clash sulle porte. Avvia kubernetes con:

```
export K8S_VERSION=1.2.2

# avvia kubernetes
docker run \
    --volume=/:/rootfs:ro \
    --volume=/sys:/sys:ro \
    --volume=/var/lib/docker/:/var/lib/docker:rw \
    --volume=/var/lib/kubelet/:/var/lib/kubelet:rw \
    --volume=/var/run:/var/run:rw \
    --net=host \
    --pid=host \
    --privileged=true \
    --name=kubelet \
    -d \
    gcr.io/google_containers/hyperkube-amd64:v${K8S_VERSION} \
    /hyperkube kubelet \
        --containerized \
        --hostname-override="127.0.0.1" \
        --address="0.0.0.0" \
        --api-servers=http://localhost:8080 \
        --config=/etc/kubernetes/manifests \
        --cluster-dns=10.0.0.10 \
        --cluster-domain=cluster.local \
        --allow-privileged=true --v=2
```

Ora possiamo scaricare lo strumento di controllo `kubectl` con:

```
cd /usr/local/bin
wget http://storage.googleapis.com/kubernetes-release/release/v${K8S_VERSION}/bin/linux/amd64/kubectl
```

`kubectl` è lo strumento da CLI che, comunicando con le API di kubernetes, ci permette di controllare tutto nel cluster.


### Running containers

I container possono venir eseguiti in diversi modi, principalmente:

- come **singoli pod**
- all'interno di **ReplicationControllers**, che si occupano di eseguire più copie dei pod, se richiesto, e di ri-schedularli in caso di fallimento
- all'interno di un **Deployment**, astrazione nuova e di più alto livello rispetto ai replication controllers

### Rolling updates

Prima di tutto abbiamo bisogno di costruire le immagini necessarie. Entrate in `v1` e `v2` ed eseguite `./build.sh`.

Lanciamo un replication controller con:

```
$ cd v1
$ kubectl create -f kitten-rc.yml
replicationcontroller "kitten" created
```

Potete verificare i pod creati con:

```
kubectl get pods
```

Oppure vedere i container con `docker ps`. Il pod è composto da 2 container: un servizio aiohttp e un container che fa semplicemente una sleep. Possiamo entrare nel container "sleep" con:

```
$ kubectl exec -c python -it kitten-9fopn python
Python 3.5.1 (default, Jan 26 2016, 05:51:15)
[GCC 4.9.2] on linux
>>> from urllib.request import urlopen
>>> urlopen('http://localhost:6000').read()
b'Meowwww'
```

:) Condivisione dei namespace! :)

### Rolling update

Per fare rolling update:

```
kubectl rolling-update --container kitten kitten-v1 kitten-v2 --image=pyconsette/kitten:v2 --update-period 10s
```

Potete monitorare i pod con il solito comando e vedere che i pod nuovi vengono creati e i vecchi vengono terminati.

### Deployments

I deployment offrono un'interfaccia più ad alto livello permettendoci un'astrazione sui replication controller.

Avviamo un deployment con:

```
kubectl create -f v1/kitten-deployment.yml --record
```

Il `--record` fa in modo che nei metadati delle risorse create venga tenuto traccia delle modifiche effettuate al deployment.

Possiamo aggiornarlo con:

```
kubectl apply -f v2/kitten-deployment.yml
```

Oppure modificando direttamente la configurazione del deployment con:

```
kubectl edit deployment/kitten
```

Alcuni comandi utili:

```
$ kubectl rollout history deployment/kitten
deployments "kitten":
REVISION    CHANGE-CAUSE
1       kubectl create -f kitten-deployment.yml --record
2       kubectl apply -f kitten-deployment.yml
```

Per vedere i dettagli di una revisione:

```
$ kubectl rollout history deployment/kitten --revision=2
deployments "kitten" revision 2
Labels:     app=kitten,pod-template-hash=1822253763
Annotations:    kubernetes.io/change-cause=kubectl apply -f kitten-deployment.yml
Image(s):   pyconsette/kitten:v2,python:3.5-slim
No volumes.
```

```
$ kubectl describe deployment/kitten
Name:           kitten
Namespace:      default
CreationTimestamp:  Fri, 15 Apr 2016 07:08:21 +0200
Labels:         app=kitten
Selector:       app=kitten
Replicas:       2 updated | 2 total | 2 available | 0 unavailable
StrategyType:       RollingUpdate
MinReadySeconds:    0
RollingUpdateStrategy:  1 max unavailable, 1 max surge
OldReplicaSets:     <none>
NewReplicaSet:      kitten-1822253763 (2/2 replicas created)
Events:
  FirstSeen LastSeen    Count   From                SubobjectPath   Type        Reason          Message
  --------- --------    -----   ----                -------------   --------    ------          -------
  1m        1m      1   {deployment-controller }            Normal      ScalingReplicaSet   Scaled up replica set kitten-1703436994 to 2
  55s       55s     1   {deployment-controller }            Normal      ScalingReplicaSet   Scaled up replica set kitten-1822253763 to 1
  55s       55s     1   {deployment-controller }            Normal      ScalingReplicaSet   Scaled down replica set kitten-1703436994 to 1
  55s       55s     1   {deployment-controller }            Normal      ScalingReplicaSet   Scaled up replica set kitten-1822253763 to 2
  53s       53s     1   {deployment-controller }            Normal      ScalingReplicaSet   Scaled down replica set kitten-1703436994 to 0
```

### Services

Abbiamo adesso un deploy della nostra App, ma come facciamo a renderla raggiungibile? Con il cluster locale che stiamo usando non ne ho idea... (se ce l'avete, ditemelo!).

Un'altro tipo di risorsa di Kubernetes è il **Service**. Esistono 2 tipi principali di service:

- app **interna** al cluster: service di tipo `NodePort`
- app **esposta** all'esterno: service di tipo `LoadBalancer`

La configurazione di un service prevede che si specifichi:

- una label **selector** per selezionare i pod
- la **porta** dei pod

Il tipo **NodePort** fa in modo che su tutti i nodi del cluster Kubernetes venga esposto il servizio su una porta specificata. Il traffico verrà poi "routato" da questa porta ai pod che offrono il servizio.

Il tipo **LoadBalancer** è invece un'astrazione del load balancer offerto dal cloud provider, ad esempio su EC2 viene creato un [Amazon ELB](https://aws.amazon.com/it/elasticloadbalancing/).

### Per approfondire
- [Questo video](https://www.youtube.com/watch?v=WwBdNXt6wO4) rappresenta un'introduzione più approfondita a Kubernetes, di uno dei founder di Kubernetes
- [Qualche idea](https://www.youtube.com/watch?v=PivpCKEiQOQ) su come gestire situazioni problematiche con Docker in production
