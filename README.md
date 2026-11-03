# Notes API Serverless

API Python distribuita su AWS con Terraform.

## Architettura

API Gateway HTTP API → Lambda → DynamoDB.

- Autenticazione IAM con richieste firmate SigV4.
- Ruolo Lambda con accesso limitato alla tabella e ai propri log.
- CloudWatch Logs con retention di 14 giorni.
- Allarme sugli errori Lambda.
- Stato Terraform remoto su S3 con versioning e locking nativo.

## Endpoint

| Metodo | Percorso | Operazione |
|---|---|---|
| POST | /notes | Crea una nota |
| GET | /notes/{id} | Recupera una nota |
| GET | /notes | Elenca le note |
| DELETE | /notes/{id} | Elimina una nota |

Titolo obbligatorio, massimo 200 caratteri.
Contenuto facoltativo, massimo 10.000 caratteri.

## Struttura

- notes/: logica applicativa, gestione HTTP, handler Lambda e repository.
- tests/: test automatici locali.
- infra/: infrastruttura Terraform.
- scripts/build_lambda.py: creazione del pacchetto Lambda.
- scripts/smoke_test.py: verifica end-to-end sull'API distribuita.

## Test locali

Con un ambiente virtuale Python attivo:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Build

```bash
python scripts/build_lambda.py
```

## Stato del progetto

Deploy AWS e verifica end-to-end completati.
Pipeline GitHub Actions con OIDC in preparazione.

## Limiti attuali

L'elenco legge tutta la tabella: questa versione è pensata per piccoli
volumi di laboratorio. L'allarme è visibile in CloudWatch; non sono
configurate notifiche email. Il progetto può generare costi AWS.
