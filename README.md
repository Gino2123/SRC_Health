# Health V1

Monorepo de démarrage pour une API FastAPI, une interface Next.js et une application Flutter.

## Stack et structure

- `backend/` — Python 3.12, FastAPI, SQLAlchemy 2 async, Alembic, Pydantic v2
- `web/` — Next.js App Router, React et TypeScript
- `mobile/` — Flutter, Riverpod et go_router
- `docker-compose.yml` — PostgreSQL et Redis pour le développement local

L'authentification est organisée côté backend en routes API, contrôleurs et services. L'inscription et la connexion sont disponibles sur le web et le mobile. L'API émet un jeton d'accès court et un jeton de renouvellement révocable.

PostgreSQL est configuré en `UTF8` ; `utf8mb4` est le nom d'un encodage MySQL.
Redis sert ici au cache et au traitement rapide, pas au stockage durable de fichiers. Le choix du stockage de fichiers sera à préciser quand cette fonctionnalité sera définie.

## Services locaux

Dans PowerShell, à la racine :

```powershell
Copy-Item .env.example .env
docker compose up -d
```

Le mot de passe fourni est réservé au développement local. Remplacez-le avant tout usage partagé ou déploiement.

## Lancer les applications

- API : suivre [backend/README.md](./backend/README.md)
- Web : suivre [web/README.md](./web/README.md)
- Mobile : suivre [mobile/README.md](./mobile/README.md)
