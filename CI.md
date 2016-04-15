
## build con docker-compose

L'altro caso d'uso per cui non farei mai a meno di docker-compose è la build, nel mio caso su jenkins.

L'esempio è simile al precedente, però in questo caso non è necessario fare bind delle porte su localhost. Inoltre dovrò aggiungere anche il container con l'applicazione. Inoltre c'è un trucco da ricordare, spiegato nella prossima sezione.

### Terminare il docker-compose al termine dei test

Quel che vogliamo fare è:

- avviare i container requirement
- avviare i test
- terminare i container requirement

Quel che vorremmo fare è qualcosa come:

```
app:
  ...
  command: py.test

elasticsearch:
  ...
```

Se lancio i test con `docker-compose up` vengono fatti partire tutti i container, i test girano ma il docker-compose non termina mai. Infatti quando il container con i test esce, il docker-compose non esce perché elasticsearch è ancora running.

Il trucco consiste nel mettere un comando *fake* nel container con i test, e avviarli esternamente:

```
app:
  ...
  command: "echo 'fake command following suggestion on https://github.com/docker/compose/pull/1754#issuecomment-154218084'"
  ...
```

```
docker-compose rm -f
docker-compose build

docker-compose up --timeout 1 --no-build -d
docker-compose run django /some/where/test.sh
docker-compose stop
```

## docker-compose multipli

È possibile specificare quale `docker-compose.yml` utilizzare tramite il flag `-f`:

```
docker-compose -f docker-compose-jenkins.yml up
```

oppure anche tramite variabile d'ambiente `COMPOSE_FILE`.

## Esercizio 2: far girare i test dell'applicazione tramite docker-compose

I test potete farli girare con il comando `py.test` dopo averlo installato:

- `pip install pytest`
