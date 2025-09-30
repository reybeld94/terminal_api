# MIE Trak Terminal API

API REST minimalista construida con FastAPI para orquestar los Stored Procedures de MIE Trak necesarios para registrar entradas y salidas de órdenes de trabajo.

## Requisitos

- Python 3.11
- SQL Server accesible mediante `pymssql`
- Variables de entorno definidas (`.env`)

## Configuración

1. Copia `.env.example` a `.env` y ajusta los valores según tu entorno.
2. Instala las dependencias:

```bash
make install
```

## Ejecución local

```bash
make run
```

El servicio quedará disponible en `http://localhost:8000`. La documentación interactiva se encuentra en `/docs` y el esquema OpenAPI en `/openapi.json`.

## Pruebas

```bash
make test
```

## Docker

Construye la imagen y levanta el contenedor:

```bash
docker build -t mie-terminal-api .
docker run --env-file .env -p 8000:8000 mie-terminal-api
```

## Licencia

Distribuido bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE).
