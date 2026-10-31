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
