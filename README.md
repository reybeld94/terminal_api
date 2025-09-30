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

## Comandos Make

- `make install`: instala dependencias en el entorno activo.
- `make run`: levanta la API en `http://127.0.0.1:8000`.
- `make test`: ejecuta la suite de tests con `pytest`.
- `make lint`: ejecuta `ruff`.
- `make fmt`: formatea con `black` e `isort`.

## Docker

Construir y ejecutar la API:

```bash
docker compose up --build
```

La API quedará disponible en `http://localhost:8000`.
