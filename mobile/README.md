# Application mobile

Application Flutter en Dart, avec Riverpod pour l'état et go_router pour la navigation.

Les projets natifs Android et iOS sont générés. Pour exécuter l'application Android, installez Android Studio et le SDK Android ; le build iOS nécessite macOS et Xcode.

Depuis la racine du monorepo, dans PowerShell :

```powershell
Set-Location mobile
flutter pub get
flutter test
flutter run
```

Le point d'entrée est `lib/main.dart`. Le SDK Flutter est installé sous `%USERPROFILE%\development\flutter` et ajouté au `PATH` utilisateur ; ouvrez un nouveau terminal pour que le changement de `PATH` soit pris en compte.

L'écran d'accueil permet de créer un compte et `/login` permet de se connecter. L'application reçoit les jetons de l'API et les conserve avec `flutter_secure_storage` dans le Keychain iOS ou le Keystore Android. L'API doit être démarrée et les migrations appliquées. Par défaut, l'émulateur Android contacte l'API de l'ordinateur via `http://10.0.2.2:8000`; Flutter Web et le simulateur iOS utilisent `http://localhost:8000`. Pour Flutter Web, ajoutez aussi son origine à `CORS_ORIGINS` dans le `.env` racine. Pour une autre adresse d'API, lancez par exemple `flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000`.

L'application Android autorise HTTP uniquement dans le manifeste `debug`, pour les tests locaux. Ne réutilisez pas cette configuration pour une version de production ; utilisez HTTPS.
