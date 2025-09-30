# Terminal API

Proyecto FastAPI minimalista para gestionar el fichaje de órdenes de trabajo.

## Requisitos

- Python 3.11
- [Poetry](https://python-poetry.org/) no es necesario; se usa `venv` estándar
- Docker (opcional)

## Configuración local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edita `.env` con las credenciales reales.

## Autenticación y tokens

En entorno de desarrollo (`ENV=dev`) la API expone un endpoint auxiliar para
generar un token JWT válido:

```bash
export ENV=dev  # o configúralo en tu archivo .env
make run &      # arranca la API en otra terminal si lo prefieres

curl http://127.0.0.1:8000/dev/token
# {"token": "<jwt>"}
```

El token está firmado con `JWT_SECRET` y utiliza los valores `JWT_ISSUER` y
`JWT_AUDIENCE` configurados en tu `.env`. Puedes reutilizarlo en las llamadas a
los endpoints protegidos mediante el header `Authorization: Bearer <jwt>`.
El ejemplo de cURL que sigue usa [`jq`](https://stedolan.github.io/jq/) para
extraer el token de la respuesta JSON; si no lo tienes instalado, copia el valor
manualmente.

## Comandos Make

- `make install`: instala dependencias en el entorno activo.
- `make run`: levanta la API en `http://127.0.0.1:8000`.
- `make test`: ejecuta la suite de tests con `pytest`.
- `make lint`: ejecuta `ruff`.
- `make fmt`: formatea con `black` e `isort`.

## Logs

El middleware de la aplicación imprime un log JSON por cada request en `stdout` con los
campos `time`, `level`, `request_id`, `method`, `path`, `status_code` y `latency_ms`.
Puedes verlos ejecutando la API de manera interactiva:

```bash
make run
```

o siguiendo los logs del contenedor si usas Docker:

```bash
docker compose logs -f
```

## Docker

Construir y ejecutar la API:

```bash
docker compose up --build
```

La API quedará disponible en `http://localhost:8000`.

## Ejemplos con cURL

```bash
# Clock-in
TOKEN="$(curl -s http://localhost:8000/dev/token | jq -r .token)"

curl -X POST http://localhost:8000/clock-in \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "workOrderAssemblyId": 1,
    "userId": 42,
    "divisionFK": 7,
    "deviceDate": "2024-01-01T08:00:00"
  }'

# Clock-out
curl -X POST http://localhost:8000/clock-out \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "workOrderCollectionId": 123,
    "quantity": 10,
    "quantityScrapped": 0,
    "scrapReasonPK": 1,
    "complete": true,
    "comment": "Proceso finalizado",
    "deviceTime": "2024-01-01T12:00:00",
    "divisionFK": 7
  }'
```
