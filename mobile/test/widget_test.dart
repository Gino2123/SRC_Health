import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:health_v1_mobile/main.dart';

void main() {
  testWidgets('affiche le formulaire d’inscription', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: HealthApp()));

    expect(find.text('Health V1'), findsOneWidget);
    expect(find.text('Créer un compte'), findsOneWidget);
    expect(find.text('Adresse e-mail'), findsOneWidget);
    expect(find.text('Créer mon compte'), findsOneWidget);
  });

  testWidgets('valide le mot de passe avant d’appeler l’API', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: HealthApp()));

    await tester.tap(find.text('Créer mon compte'));
    await tester.pumpAndSettle();

    expect(find.text('Saisissez votre adresse e-mail.'), findsOneWidget);
    expect(
      find.text('Le mot de passe doit contenir au moins 12 caractères.'),
      findsOneWidget,
    );
  });

  testWidgets('ouvre la page de connexion', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: HealthApp()));

    await tester.tap(find.text('Déjà un compte ? Se connecter'));
    await tester.pumpAndSettle();

    expect(find.text('Connexion'), findsOneWidget);
    expect(find.text('Se connecter'), findsOneWidget);
  });
}
