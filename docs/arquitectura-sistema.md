# Arquitectura del Sistema

## Documento de Diseño Arquitectonico

**Proyecto:** Sistema Backend - Gestion de Productos, Ordenes y Reportes de Ventas

**Fecha:** 14 de febrero de 2026

**Autor:** Jamid Stiven Villarreal Rugeles

**Arquitectura:** Hexagonal (Ports & Adapters)

## Requerimientos Técnicos

**Lenguaje:** Python

**Framework:** FastAPI

**Base de datos:** PostgreSQL

**ORM:** SQLAlchemy

**Redis:** redis

**Validaciones:** Pydantic

**Manejo correcto de errores HTTP**

**Control de transacciones**

---

## Tabla de Contenidos

1. [Diagrama de Flujo del Sistema](#1-diagrama-de-flujo-del-sistema)
2. [Componentes Principales](#2-componentes-principales)
3. [Justificacion del Stack Tecnologico](#3-justificacion-del-stack-tecnologico)
4. [Flujo de Creacion de Ordenes](#4-flujo-de-creacion-de-ordenes)
5. [Uso de Redis](#5-uso-de-redis)
6. [Estrategia de Escalabilidad](#6-estrategia-de-escalabilidad)

---

## 1. Diagrama de Flujo del Sistema

### 1.1 Arquitectura general

![diagrama arquitectura](./img//Diagrama-flujo-sistema-draw.png)

### 1.2 Flujo de una Request HTTP

![diagrama flujo http](./img/flujo-request-http.png)

## 2. Componentes Principales

### 2.1 API Backend (FastAPI)

FastAPI actua como el adaptador primario de entrada en la arquitectura hexagonal.

#### Estructura Hexagonal del proyecto

```text
app/
├── main.py                          # Entry point
├── api/                             # ADAPTERS IN
│   ├── v1/endpoints/
│   │   ├── products.py
│   │   ├── orders.py
│   │   └── reports.py
│   ├── dependencies.py              # Inyeccion de dependencias
│   └── middleware/
│       ├── rate_limiter.py
│       ├── logging_middleware.py
│       └── error_handler.py
├── domain/                          # NUCLEO DEL HEXAGONO
│   ├── models/
│   │   ├── product.py
│   │   └── order.py
│   ├── services/
│   │   ├── product_service.py
│   │   ├── order_service.py
│   │   └── report_service.py
│   ├── ports/outbound/
│   │   ├── product_repository_port.py
│   │   ├── order_repository_port.py
│   │   └── cache_port.py
│   └── exceptions.py
├── infrastructure/                  # ADAPTERS OUT
│   ├── database/
│   │   ├── connection.py
│   │   ├── models/
│   │   └── repositories/
│   └── cache/
│       ├── redis_client.py
│       └── redis_cache_adapter.py
├── schemas/                         # Pydantic DTOs
└── core/
    ├── config.py
    └── logging.py
```

#### Responsabilidades de cada capa

| Capa                             | Responsabilidad                                   | Depende de              |
| -------------------------------- | ------------------------------------------------- | ----------------------- |
| `api/` (Adapters In)             | Recibir HTTP, validar entrada, devolver responses | `domain/ports`          |
| `domain/ports/`                  | Definir contratos (interfaces abstractas)         | Nada                    |
| `domain/services/`               | Logica de negocio, reglas, orquestacion           | `domain/ports/outbound` |
| `domain/models/`                 | Entidades del negocio con invariantes             | Nada                    |
| `infrastructure/` (Adapters Out) | Acceso a datos, cache, servicios externos         | `domain/ports/outbound` |
| `schemas/`                       | DTOs de entrada/salida (Pydantic)                 | Nada                    |

**Regla de dependencia:** Las flechas siempre apuntan hacia el dominio. La infraestructura depende del dominio, nunca al reves.

### 2.2 Base de Datos Relacional (PostgreSQL)

#### Modelo Entidad-Relacion

![MER base de datos](./img/modelo-entidad-relacion-mer.png)

#### Estados de una orden

![estado de orden](./img/estado-orden.png)

### 2.3 Redis

| Funcion                | Patron de clave                | TTL    | Proposito                        |
| ---------------------- | ------------------------------ | ------ | -------------------------------- |
| **Cache de productos** | `product:{id}`                 | 5 min  | Evitar queries repetitivos       |
| **Cache de listados**  | `products:list:{skip}:{limit}` | 2 min  | Acelerar listados paginados      |
| **Cache de reportes**  | `report:{type}:{params_hash}`  | 10 min | Reportes costosos pre-calculados |
| **Rate Limiting**      | `rate:{client_ip}`             | 1 min  | Control de abuso                 |
| **Locks distribuidos** | `lock:stock:{product_id}`      | 30 seg | Concurrencia en stock            |

### 2.4 Capa de Autenticacion

![capa-autenticacion](./img/diagrama-capa-autenticacion.jpg)

## 3. Justificacion del Stack Tecnologico

### 3.1 Framework: FastAPI

| Criterio              | FastAPI             | Flask          | Django REST     |
| --------------------- | ------------------- | -------------- | --------------- |
| **Rendimiento**       | Alto (async nativo) | Medio (sync)   | Medio           |
| **Validacion**        | Pydantic integrado  | Manual         | DRF Serializers |
| **Docs auto**         | OpenAPI/Swagger     | Manual         | Browsable API   |
| **Async nativo**      | Si                  | Limitado       | Limitado        |
| **Inyeccion de deps** | Built-in (Depends)  | Flask-Injector | Limitado        |

**Decision:** FastAPI

1. **Async nativo** para manejar miles de conexiones concurrentes.
2. **Pydantic integrado** valida cada request antes de la logica de negocio.
3. **Swagger auto-generado** desde type hints, acelera integracion con frontend.
4. **`Depends()`** facilita la arquitectura hexagonal al inyectar repositorios y servicios.
5. **Rendimiento** comparable a Node.js/Go (basado en Starlette + Uvicorn ASGI).

### 3.2 Base de Datos: PostgreSQL

| Criterio               | PostgreSQL                  | MySQL      | SQLite          |
| ---------------------- | --------------------------- | ---------- | --------------- |
| **Transacciones ACID** | Completo                    | Completo   | Parcial         |
| **Concurrencia**       | MVCC avanzado               | Lock-based | Lock global     |
| **Escalabilidad**      | Read replicas, partitioning | Buena      | Solo desarrollo |

**Decision:** PostgreSQL

1. **MVCC:** Lecturas no bloquean escrituras. Reportes corren mientras se procesan ordenes.
2. **`SELECT FOR UPDATE`:** Lock a nivel de fila para proteger stock en ordenes.
3. **DECIMAL:** Sin errores de punto flotante en precios.
4. **Escalabilidad:** Read replicas + PgBouncer para alta concurrencia.

### 3.3 ORM: SQLAlchemy (Async)

| Criterio        | SQLAlchemy | SQLModel | Tortoise |
| --------------- | ---------- | -------- | -------- |
| **Madurez**     | 20+ anos   | Reciente | Medio    |
| **Async**       | Si (v2.0+) | Parcial  | Nativo   |
| **Migraciones** | Alembic    | Alembic  | Aerich   |

**Decision:** SQLAlchemy 2.0+

1. **AsyncSession** se integra con el event loop de FastAPI sin bloquear.
2. **Unit of Work:** Control fino de transacciones para atomicidad en ordenes.
3. **Alembic:** Migraciones versionadas y reversibles.

### 3.4 Redis: Por que y Para que

| Rol               | Problema sin Redis                                             | Solucion con Redis                                                      |
| ----------------- | -------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **Cache**         | 1000 req/s, cada una query a PostgreSQL. DB se satura.         | `GET product:123` en ~0.1ms vs ~5ms de PostgreSQL.                      |
| **Concurrencia**  | Dos usuarios compran el ultimo item. Stock queda negativo.     | `SET lock:stock:456 NX EX 30` — lock atomico distribuido.               |
| **Rate Limiting** | Cliente abusivo con 10K req/s degrada el servicio.             | `INCR rate:ip` con TTL 60s. HTTP 429 si excede limite.                  |
| **Reportes**      | Query de ventas escanea 100K registros. 50 usuarios = 5M rows. | Primer request cachea el resultado. Siguientes 49 lo obtienen en 0.1ms. |

**Driver:** `redis.asyncio` para integracion nativa con el event loop.

## 4. Flujo de Creacion de Ordenes

TODO

## 5. Uso de Redis

TODO

## 6. Estrategia de Escalabilidad

TODO
