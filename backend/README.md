# API backend

Prérequis : Python 3.12.

Depuis la racine du monorepo, dans PowerShell :

```powershell
py -3.12 -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install -e "backend[dev]"
uvicorn app.main:app --reload --app-dir backend
```

`GET /health` vérifie le démarrage de l'API. Le modèle `users` et sa migration Alembic initiale sont inclus.

`POST /auth/register` crée un compte à partir d'une adresse e-mail et d'un mot de passe d'au moins 12 caractères. L'adresse est normalisée en minuscules ; le mot de passe est stocké sous forme de hash Argon2id et n'est jamais renvoyé par l'API. Une adresse déjà utilisée renvoie `409 Conflict`. La création d'un compte ne connecte pas encore l'utilisateur : il doit ensuite utiliser `POST /auth/login`.

## Architecture de l'authentification

- `app/api/auth.py` déclare les routes HTTP et leurs dépendances FastAPI.
- `app/controllers/auth_controller.py` gère les réponses HTTP et les cookies sécurisés pour le navigateur.
- `app/services/auth_service.py` contient les règles d'inscription, de connexion, de renouvellement et de révocation.
- `app/models.py` définit les tables `users` et `refresh_sessions`.
- `app/schemas.py` valide les données entrantes et définit les réponses publiques.
- `app/security.py` hache les mots de passe et signe/vérifie les jetons d'accès.
- `app/dependencies.py` identifie l'utilisateur à partir d'un jeton d'accès.

## Connexion et sessions

- `POST /auth/login` vérifie l'e-mail et le mot de passe. Le jeton d'accès JWT expire après 15 minutes. Le jeton de renouvellement aléatoire expire après 30 jours et n'est enregistré en base que sous forme de hash.
- `POST /auth/refresh` remplace le jeton de renouvellement par un nouveau. Réutiliser un ancien jeton révoque toute sa famille de sessions.
- `POST /auth/logout` révoque la session correspondant au jeton de renouvellement. Le jeton d'accès déjà émis peut rester valable jusqu'à son expiration, au plus 15 minutes.
- `GET /auth/me` renvoie le profil associé à un jeton d'accès.

Le navigateur envoie `X-Auth-Transport: cookie` : l'API place les deux jetons dans des cookies `HttpOnly`, sans exposer leur valeur au JavaScript. Les appels web utilisent `credentials: "include"`, et l'API vérifie l'origine autorisée pour ces opérations. L'application mobile reçoit les jetons dans la réponse JSON et les conserve avec `flutter_secure_storage` dans le stockage natif sécurisé Android/iOS ; le jeton d'accès est envoyé dans `Authorization: Bearer ...`.

Une clé de signature doit être définie localement dans `.env` avec `JWT_SECRET_KEY` (au moins 32 caractères aléatoires). Une clé locale peut être générée avec :

```powershell
py -c "import secrets; print(secrets.token_urlsafe(48))"
```

Ne publiez jamais cette valeur. En production, configurez `COOKIE_SECURE=true` et déployez l'API en HTTPS. Si le site et l'API sont sur des sites différents, configurez également `COOKIE_SAMESITE=none` et des origines exactes dans `CORS_ORIGINS`.

Les principales routes sont disponibles dans `/docs` lorsque l'API tourne.

Les migrations versionnées créent `users` puis `refresh_sessions`. Appliquez toutes les migrations après le démarrage de PostgreSQL :

```powershell
alembic -c backend\alembic.ini upgrade head
```

Exemple de création d'un compte :

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/auth/register `
  -ContentType "application/json" `
  -Body '{"email":"personne@example.com","password":"un-mot-de-passe-solide"}'
```

Les paramètres `DATABASE_URL`, `REDIS_URL` et `CORS_ORIGINS` sont lus depuis les variables d'environnement ou le `.env` placé à la racine. `CORS_ORIGINS` est une liste JSON d'origines autorisées ; adaptez-la au domaine du site avant un déploiement. Après création ou modification des modèles, générez une migration depuis la racine :

```powershell
alembic -c backend\alembic.ini revision --autogenerate -m "describe change"
alembic -c backend\alembic.ini upgrade head
```
