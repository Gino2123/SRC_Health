# API backend

Prérequis : Python 3.12.

Depuis la racine du monorepo, dans PowerShell :

```powershell
py -3.12 -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install -e "backend[dev]"
uvicorn app.main:app --reload --app-dir backend
```

`GET /health` vérifie le démarrage de l'API. La fabrique de sessions SQLAlchemy async, le client Redis et l'environnement de migrations Alembic sont prêts pour les premiers modèles métier.

Les paramètres `DATABASE_URL` et `REDIS_URL` sont lus depuis les variables d'environnement ou le `.env` placé à la racine. Après création des modèles, générez une migration depuis la racine :

```powershell
alembic -c backend\alembic.ini revision --autogenerate -m "initial"
alembic -c backend\alembic.ini upgrade head
```
