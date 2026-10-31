import 'package:flutter_test/flutter_test.dart';
import 'package:health_v1_mobile/main.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

void main() {
  testWidgets('affiche la page d’accueil', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: HealthApp()));

    expect(find.text('Health V1'), findsOneWidget);
    expect(find.text('Bienvenue'), findsOneWidget);
  });
}
