# Product Management API

Backend service para gestion de productos, ordenes de compra y reportes de ventas.
Construido con FastAPI, PostgreSQL, Redis y arquitectura hexagonal.

## Tabla de Contenidos

- [Instrucciones de Ejecucion](#instrucciones-de-ejecucion)
- [Endpoints](#endpoints)
- [Decisiones Tecnicas](#decisiones-tecnicas)
- [Uso Especifico de Redis](#uso-especifico-de-redis)
- [Tests](#tests)
- [Estructura del Proyecto](#estructura-del-proyecto)

---

## Instrucciones de Ejecucion

### Requisitos Previos

- Docker y Docker Compose **o**
- Python 3.12+, PostgreSQL 16, Redis 7

### Opcion 1: Docker Compose (recomendado)

```bash
# Clonar y entrar al proyecto
cd commerce-core

# Levantar los 3 servicios (API + PostgreSQL + Redis)
docker compose up --build

# La API estara disponible en http://localhost:8000
# Documentacion Swagger en http://localhost:8000/docs
# Documentacion ReDoc en http://localhost:8000/redoc
```

Para detener:

```bash
docker compose down

# Para eliminar tambien los volumenes de datos:
docker compose down -v
```

### Opcion 2: Ejecucion Local

```bash
# Crear entorno virtual e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de PostgreSQL y Redis

# Ejecutar migraciones
alembic upgrade head

# Iniciar el servidor
uvicorn app.main:app --reload
```

### Variables de Entorno

| Variable                          | Descripcion                               | Default                                                            |
| --------------------------------- | ----------------------------------------- | ------------------------------------------------------------------ |
| `DATABASE_URL`                    | URL de conexion a PostgreSQL              | `postgresql+asyncpg://postgres:postgres@localhost:5432/product_db` |
| `REDIS_URL`                       | URL de conexion a Redis                   | `redis://localhost:6379/0`                                         |
| `DEBUG`                           | Modo debug (logs detallados)              | `false`                                                            |
| `RATE_LIMIT_PER_MINUTE`           | Limite de requests por IP/minuto          | `60`                                                               |
| `JWT_SECRET_KEY`                  | Clave secreta para firmar tokens JWT      | `change-me-in-production`                                          |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Tiempo de expiracion del token en minutos | `30`                                                               |

---

## Endpoints

> Todos los endpoints excepto `/auth/register` y `/auth/login` requieren autenticacion JWT.
> Enviar el header `Authorization: Bearer <token>` obtenido del login.

### Autenticacion

| Metodo | Ruta                    | Descripcion                 |
| ------ | ----------------------- | --------------------------- |
| `POST` | `/api/v1/auth/register` | Registrar nuevo usuario     |
| `POST` | `/api/v1/auth/login`    | Login (devuelve JWT token)  |
| `GET`  | `/api/v1/auth/me`       | Obtener usuario autenticado |

### Productos

| Metodo | Ruta                                    | Descripcion                           |
| ------ | --------------------------------------- | ------------------------------------- |
| `POST` | `/api/v1/products/`                     | Crear producto                        |
| `GET`  | `/api/v1/products/?page=1&page_size=20` | Listar productos (paginado, cacheado) |

### Ordenes

| Metodo | Ruta                  | Descripcion                                        |
| ------ | --------------------- | -------------------------------------------------- |
| `POST` | `/api/v1/orders/`     | Crear orden (valida stock, descuenta atomicamente) |
| `GET`  | `/api/v1/orders/{id}` | Obtener orden por ID con detalle de items          |

### Reportes

| Metodo | Ruta                                                  | Descripcion                           |
| ------ | ----------------------------------------------------- | ------------------------------------- |
| `GET`  | `/api/v1/reports/top-products?limit=10`               | Productos mas vendidos                |
| `GET`  | `/api/v1/reports/sales?from=2026-01-01&to=2026-01-31` | Reporte de ventas por rango de fechas |

### Ejemplos con cURL

```bash
# Registrar usuario
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "mypassword123", "full_name": "John Doe"}'

# Login (guardar el access_token)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "mypassword123"}'
# Respuesta: {"access_token": "eyJhbG...", "token_type": "bearer"}

# Obtener usuario autenticado
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"

# Crear producto (requiere token)
curl -X POST http://localhost:8000/api/v1/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"name": "Laptop Pro", "sku": "LAP-001", "price": "999.99", "stock": 50, "category": "Electronics"}'

# Listar productos (requiere token)
curl http://localhost:8000/api/v1/products/?page=1&page_size=10 \
  -H "Authorization: Bearer <token>"

# Crear orden (requiere token)
curl -X POST http://localhost:8000/api/v1/orders/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"customer_name": "Jane Doe", "customer_email": "jane@example.com", "items": [{"product_id": 1, "quantity": 3}]}'

# Obtener orden (requiere token)
curl http://localhost:8000/api/v1/orders/1 \
  -H "Authorization: Bearer <token>"

# Top productos (requiere token)
curl http://localhost:8000/api/v1/reports/top-products?limit=5 \
  -H "Authorization: Bearer <token>"

# Reporte de ventas (requiere token)
curl "http://localhost:8000/api/v1/reports/sales?from=2026-01-01&to=2026-12-31" \
  -H "Authorization: Bearer <token>"
```

---

## Decisiones Tecnicas

### Arquitectura Hexagonal (Ports & Adapters)

El proyecto separa el codigo en tres capas con una regla estricta de dependencia: **las capas externas dependen del dominio, nunca al reves**.

```
api/ (adapters in)  -->  domain/ (nucleo)  <--  infrastructure/ (adapters out)
```

- **`domain/`** contiene modelos de negocio, servicios y puertos (interfaces abstractas). No importa nada de FastAPI, SQLAlchemy ni Redis.
- **`infrastructure/`** implementa los puertos con tecnologias concretas (PostgreSQL via SQLAlchemy, Redis via redis-py).
- **`api/`** traduce HTTP requests a llamadas de dominio y viceversa.

**Por que esta separacion:** Permite reemplazar PostgreSQL por otro motor o Redis por Memcached sin tocar la logica de negocio. Los tests unitarios del dominio corren con mocks puros, sin base de datos ni Redis reales.

### FastAPI como Framework

Elegido por tres razones concretas:

1. **Async nativo.** Todas las operaciones de I/O (base de datos, Redis, HTTP) usan `async/await`, lo que permite manejar cientos de conexiones concurrentes en un solo worker sin bloquear el event loop.
2. **Validacion automatica con Pydantic.** Cada request se valida antes de llegar a la logica de negocio. Un JSON invalido nunca alcanza el servicio de dominio.
3. **`Depends()` para inyeccion de dependencias.** Los repositorios y servicios se inyectan en los endpoints sin acoplar capas. Esto hace que en tests podamos reemplazar PostgreSQL por SQLite y Redis por un diccionario en memoria con un solo `dependency_overrides`.

### PostgreSQL con SQLAlchemy Async

- **`asyncpg`** como driver: es el driver async mas rapido para PostgreSQL en Python.
- **`SELECT ... FOR UPDATE`** en el repositorio de productos: bloquea la fila a nivel de base de datos durante la transaccion de creacion de ordenes. Es la segunda capa de proteccion contra race conditions (la primera es el lock de Redis).
- **`AsyncSession` con commit/rollback automatico:** el context manager en `get_db()` hace commit si todo sale bien y rollback si hay excepcion. No hay commits manuales dispersos por el codigo.
- **Alembic con soporte async** para migraciones versionadas y reversibles.

### Pydantic para Validacion

Los schemas en `app/schemas/` definen contratos estrictos de entrada y salida:

- `ProductCreate` valida que `price > 0`, `stock >= 0`, `sku` no vacio.
- `OrderCreate` valida `EmailStr`, lista de items con `min_length=1`, `quantity > 0`.
- Los query params de reportes validan formato de fecha con regex `^\d{4}-\d{2}-\d{2}$`.

Si la validacion falla, FastAPI responde HTTP 422 con detalle del error **antes** de que el request llegue al servicio.

### Manejo de Errores

Un middleware global (`ErrorHandlerMiddleware`) captura excepciones de dominio y las traduce a HTTP:

| Excepcion de Dominio      | Codigo HTTP | Cuando Ocurre                                          |
| ------------------------- | ----------- | ------------------------------------------------------ |
| `ProductNotFoundError`    | 404         | Producto no existe                                     |
| `OrderNotFoundError`      | 404         | Orden no existe                                        |
| `InsufficientStockError`  | 409         | Stock insuficiente para la cantidad solicitada         |
| `StockLockError`          | 409         | Otro proceso esta modificando el stock del producto    |
| `UserAlreadyExistsError`  | 409         | Email ya registrado                                    |
| `InvalidCredentialsError` | 401         | Email o password incorrectos                           |
| `UserNotFoundError`       | 404         | Usuario no encontrado                                  |
| Cualquier otra excepcion  | 500         | Error no esperado (se loguea, no se expone al cliente) |

### Logs Estructurados

Se usa `structlog` con salida en JSON. Cada log incluye contexto automatico:

```json
{"event": "order_created", "order_id": 42, "total": "150.00", "items_count": 3, "timestamp": "2026-02-14T..."}
{"event": "http_request", "method": "POST", "path": "/api/v1/orders/", "status_code": 201, "elapsed_ms": 12.5}
{"event": "rate_limit_exceeded", "client_ip": "192.168.1.1", "count": 61}
```

Esto facilita el analisis con herramientas como ELK, Datadog o CloudWatch en produccion.

---

## Uso Especifico de Redis

Redis cumple cuatro roles distintos en el sistema. Todos operan de forma **async** via `redis.asyncio` para no bloquear el event loop de FastAPI.

### 1. Cache de Productos (patron Cache-Aside)

**Problema:** Cada `GET /products/` sin cache ejecuta un query a PostgreSQL. Con alta concurrencia, la base de datos se satura con lecturas repetitivas.

**Solucion:** El `ProductService` busca primero en Redis. Solo va a PostgreSQL en caso de miss.

```
GET /api/v1/products/?page=1&page_size=20

  1. Redis GET "products:list:0:20"
     -> HIT:  retornar JSON cacheado (~0.1ms)
     -> MISS: continuar paso 2

  2. PostgreSQL SELECT ... OFFSET 0 LIMIT 20 (~5ms)

  3. Redis SET "products:list:0:20" (valor JSON) EX 120
     -> TTL de 2 minutos

  4. Retornar resultado
```

**Claves utilizadas:**

| Clave                          | TTL   | Contenido                       |
| ------------------------------ | ----- | ------------------------------- |
| `product:{id}`                 | 5 min | JSON de un producto individual  |
| `products:list:{skip}:{limit}` | 2 min | JSON con lista paginada + total |

**Invalidacion:** Cuando se crea un producto o se modifica stock (al crear una orden), se eliminan las claves afectadas:

```python
# Al crear producto:
await cache.delete_pattern("products:list:*")

# Al crear orden (stock cambio):
await cache.delete(f"product:{pid}")
await cache.delete_pattern("products:list:*")
```

El patron es **invalidacion activa**, no expiracion pasiva. Esto garantiza que el usuario nunca ve stock desactualizado despues de una compra.

### 2. Locks Distribuidos para Concurrencia de Stock

**Problema:** Dos usuarios compran el ultimo item al mismo tiempo. Ambos leen `stock=1`, ambos validan, ambos decrementan. Resultado: `stock=-1`.

**Solucion:** Doble barrera: lock en Redis + `SELECT FOR UPDATE` en PostgreSQL.

```
Usuario A: POST /orders/ (producto 42, qty=1)
Usuario B: POST /orders/ (producto 42, qty=1)

Tiempo  Usuario A                          Usuario B
  t1    SET lock:stock:42 NX EX 30 -> OK   SET lock:stock:42 NX EX 30 -> FAIL
  t2    SELECT stock FOR UPDATE             -> HTTP 409 "StockLockError"
  t3    stock=1, OK
  t4    UPDATE stock=0
  t5    COMMIT
  t6    DEL lock:stock:42
```

**Detalles de implementacion:**

- `SET key NX EX 30`: `NX` = solo si no existe (atomico). `EX 30` = expira en 30 segundos (previene deadlocks si el proceso muere).
- Los product IDs se **ordenan antes de adquirir locks** (`sorted()`) para evitar deadlocks entre ordenes que comparten productos.
- Los locks se liberan en un bloque `finally`, incluso si la operacion falla.
- **Degradacion graceful:** si Redis no esta disponible, `acquire_lock` retorna `True` y el sistema depende solo de `SELECT FOR UPDATE` de PostgreSQL.

### 3. Cache de Reportes

**Problema:** Los reportes ejecutan queries con JOINs sobre miles de registros. Si 50 usuarios piden el mismo reporte, son 50 queries pesadas identicas.

**Solucion:** El primer request ejecuta la query y cachea el resultado. Los siguientes lo obtienen de Redis.

```
GET /api/v1/reports/top-products?limit=10

  1. Redis GET "report:top_products:10"
     -> HIT: retornar (~0.1ms)
     -> MISS: continuar

  2. PostgreSQL: SELECT con JOIN orders + order_items + products
     GROUP BY producto, ORDER BY total_sold DESC (~50-500ms)

  3. Redis SET "report:top_products:10" EX 600
     -> TTL de 10 minutos

  4. Retornar resultado
```

```
GET /api/v1/reports/sales?from=2026-01-01&to=2026-01-31

  1. Hash de parametros: MD5("2026-01-01:2026-01-31")[:8] = "a3f2b1c0"

  2. Redis GET "report:sales:a3f2b1c0"
     -> HIT o MISS (mismo flujo)
```

**Claves utilizadas:**

| Clave                         | TTL    | Contenido                     |
| ----------------------------- | ------ | ----------------------------- |
| `report:top_products:{limit}` | 10 min | JSON con ranking de productos |
| `report:sales:{params_hash}`  | 10 min | JSON con ventas diarias       |

**Invalidacion:** Cuando se crea una orden, todos los reportes se invalidan:

```python
await cache.delete_pattern("report:*")
```

El TTL de 10 minutos es un balance entre frescura de datos y carga en la base de datos. Para reportes historicos (meses anteriores), los datos no cambian, asi que el cache es efectivo al 100%.

### 4. Rate Limiting

**Problema:** Un cliente abusivo envia miles de requests por segundo y degrada el servicio para todos.

**Solucion:** Un middleware cuenta requests por IP usando `INCR` atomico de Redis.

```
Cada request HTTP:

  1. Redis INCR "rate:{client_ip}"
     -> Si es el primer request del minuto, SET expire 60 seg

  2. Si count > 60 (configurable):
     -> HTTP 429 "Too many requests"

  3. Si count <= 60:
     -> Request continua normalmente
```

**Clave utilizada:**

| Clave              | TTL    | Contenido                                 |
| ------------------ | ------ | ----------------------------------------- |
| `rate:{client_ip}` | 60 seg | Contador de requests en la ventana actual |

`INCR` es **atomico** en Redis, lo que significa que incluso con multiples workers de Uvicorn, el contador es exacto. El TTL de 60 segundos crea una ventana deslizante simple: al expirar la clave, el contador se reinicia automaticamente.

### Resumen de Claves Redis

| Patron de Clave                | Rol        | TTL    | Operaciones             |
| ------------------------------ | ---------- | ------ | ----------------------- |
| `product:{id}`                 | Cache      | 5 min  | GET, SET, DEL           |
| `products:list:{skip}:{limit}` | Cache      | 2 min  | GET, SET, DEL (pattern) |
| `report:top_products:{limit}`  | Cache      | 10 min | GET, SET, DEL (pattern) |
| `report:sales:{hash}`          | Cache      | 10 min | GET, SET, DEL (pattern) |
| `lock:stock:{product_id}`      | Lock       | 30 seg | SET NX, DEL             |
| `rate:{client_ip}`             | Rate Limit | 60 seg | INCR, EXPIRE            |

### Tolerancia a Fallos

Todas las operaciones de Redis estan envueltas en `try/except`. Si Redis cae:

- **Cache:** miss siempre, se consulta PostgreSQL directamente. El sistema funciona mas lento pero no se rompe.
- **Locks:** `acquire_lock` retorna `True`, delegando la proteccion a `SELECT FOR UPDATE` de PostgreSQL.
- **Rate Limiting:** se permite el request. Mejor servir que bloquear por un fallo de infraestructura.

---

## Tests

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Solo tests unitarios
pytest tests/unit/ -v

# Solo tests de integracion
pytest tests/integration/ -v
```

**41 tests** divididos en:

- **17 tests unitarios** (`tests/unit/domain/`): Prueban la logica de negocio con mocks puros. No necesitan base de datos ni Redis. Incluyen tests de `ProductService`, `OrderService` y `UserService`.
- **24 tests de integracion** (`tests/integration/`): Prueban el flujo completo HTTP -> Service -> DB. Usan SQLite en memoria y un `FakeCacheAdapter` en vez de Redis. Incluyen tests de autenticacion, productos, ordenes y reportes.

---

## Estructura del Proyecto

```
app/
├── main.py                              # Entry point, lifespan, middleware
├── api/                                 # ADAPTERS IN
│   ├── dependencies.py                  # Inyeccion de dependencias (Depends)
│   ├── middleware/
│   │   ├── error_handler.py             # Excepciones de dominio -> HTTP
│   │   ├── logging_middleware.py         # Logs de cada request
│   │   └── rate_limiter.py              # Rate limiting con Redis
│   └── v1/endpoints/
│       ├── auth.py                      # POST register/login, GET me
│       ├── products.py                  # POST/GET productos
│       ├── orders.py                    # POST/GET ordenes
│       └── reports.py                   # GET reportes
├── domain/                              # NUCLEO (sin dependencias externas)
│   ├── exceptions.py                    # Errores tipados del dominio
│   ├── models/
│   │   ├── product.py                   # Entidad Producto
│   │   ├── order.py                     # Entidad Orden + OrderItem
│   │   └── user.py                      # Entidad Usuario
│   ├── ports/outbound/
│   │   ├── product_repository_port.py   # Interface de repositorio
│   │   ├── order_repository_port.py     # Interface de repositorio
│   │   ├── user_repository_port.py      # Interface de repositorio
│   │   └── cache_port.py               # Interface de cache
│   └── services/
│       ├── product_service.py           # Logica de productos + cache
│       ├── order_service.py             # Logica de ordenes + locks + stock
│       ├── report_service.py            # Logica de reportes + cache
│       └── user_service.py             # Registro, autenticacion, consulta
├── infrastructure/                      # ADAPTERS OUT
│   ├── cache/
│   │   ├── redis_client.py              # Conexion async Redis
│   │   └── redis_cache_adapter.py       # Implementacion de CachePort
│   └── database/
│       ├── connection.py                # Engine + session async
│       ├── models/                      # Modelos SQLAlchemy ORM
│       └── repositories/               # Implementaciones de los ports
├── schemas/                             # DTOs Pydantic (request/response)
└── core/
    ├── config.py                        # Settings con pydantic-settings
    ├── security.py                      # JWT + bcrypt utilities
    └── logging.py                       # Configuracion structlog

tests/
├── unit/domain/                         # Tests con mocks (sin DB/Redis)
└── integration/                         # Tests HTTP completos (SQLite)

docker-compose.yml                       # API + PostgreSQL + Redis
alembic/                                 # Migraciones de base de datos
```
