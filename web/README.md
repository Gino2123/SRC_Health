# Application web

Application générée avec Next.js, React, TypeScript, l'App Router et Tailwind CSS.

Prérequis : Node.js 20.9 ou supérieur.

Depuis la racine du monorepo, dans PowerShell :

```powershell
Set-Location web
npm run dev
```

L'application est disponible sur <http://localhost:3000>. Pour valider le projet :

```powershell
npm run lint
npm run build
```

La page `/home` est publique et adapte son contenu si une session est active ; `/` redirige vers `/home`. L'inscription est sur `/subscribe` et la connexion sur `/login`. Les pages communiquent avec les routes `POST /auth/register` et `POST /auth/login`. Le navigateur conserve les jetons dans des cookies `HttpOnly` ; le JavaScript de la page ne peut donc pas les lire. Démarrez l'API avant d'utiliser l'inscription ou la connexion. Pour utiliser une autre adresse d'API, définissez `NEXT_PUBLIC_API_URL` avant de lancer Next.js.
