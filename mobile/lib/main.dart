import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:http/http.dart' as http;

import 'login_page.dart';

void main() {
  runApp(const ProviderScope(child: HealthApp()));
}

String get _apiBaseUrl {
  const configuredUrl = String.fromEnvironment('API_BASE_URL');
  if (configuredUrl.isNotEmpty) {
    return configuredUrl;
  }
  if (kIsWeb || defaultTargetPlatform == TargetPlatform.iOS) {
    return 'http://localhost:8000';
  }
  return 'http://10.0.2.2:8000';
}

final _router = GoRouter(
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const RegistrationPage(),
    ),
    GoRoute(
      path: '/login',
      builder: (context, state) => const LoginPage(),
    ),
  ],
);

class HealthApp extends StatelessWidget {
  const HealthApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Health V1',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal)),
      routerConfig: _router,
    );
  }
}

class RegistrationPage extends StatefulWidget {
  const RegistrationPage({super.key});

  @override
  State<RegistrationPage> createState() => _RegistrationPageState();
}

class _RegistrationPageState extends State<RegistrationPage> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmationController = TextEditingController();
  bool _isSubmitting = false;
  String? _errorMessage;
  bool _registered = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _confirmationController.dispose();
    super.dispose();
  }

  Future<void> _register() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    try {
      final response = await http
          .post(
            Uri.parse('$_apiBaseUrl/auth/register'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'email': _emailController.text.trim(),
              'password': _passwordController.text,
            }),
          )
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 201) {
        setState(() => _registered = true);
        return;
      }

      final responseBody = jsonDecode(response.body);
      final detail = responseBody is Map<String, dynamic>
          ? responseBody['detail']
          : null;
      setState(() {
        _errorMessage = detail is String
            ? detail
            : 'Vérifiez votre adresse e-mail et votre mot de passe.';
      });
    } on http.ClientException {
      setState(() {
        _errorMessage = 'Impossible de joindre le serveur. Vérifiez que l’API est démarrée.';
      });
    } on TimeoutException {
      setState(() => _errorMessage = 'Le serveur met trop de temps à répondre.');
    } on FormatException {
      setState(() => _errorMessage = 'Le serveur a renvoyé une réponse invalide.');
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Health V1')),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: _registered
                ? const Card(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Text(
                        'Votre compte a été créé. Vous pourrez vous connecter dans une prochaine étape.',
                        textAlign: TextAlign.center,
                      ),
                    ),
                  )
                : Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          'Créer un compte',
                          style: Theme.of(context).textTheme.headlineMedium,
                        ),
                        const SizedBox(height: 8),
                        const Text('Inscrivez-vous avec votre adresse e-mail.'),
                        const SizedBox(height: 24),
                        TextFormField(
                          controller: _emailController,
                          decoration: const InputDecoration(
                            labelText: 'Adresse e-mail',
                            border: OutlineInputBorder(),
                          ),
                          keyboardType: TextInputType.emailAddress,
                          autofillHints: const [AutofillHints.email],
                          validator: (value) => value == null || value.trim().isEmpty
                              ? 'Saisissez votre adresse e-mail.'
                              : null,
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _passwordController,
                          decoration: const InputDecoration(
                            labelText: 'Mot de passe (12 caractères minimum)',
                            border: OutlineInputBorder(),
                          ),
                          obscureText: true,
                          autofillHints: const [AutofillHints.newPassword],
                          validator: (value) => value == null || value.length < 12
                              ? 'Le mot de passe doit contenir au moins 12 caractères.'
                              : null,
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _confirmationController,
                          decoration: const InputDecoration(
                            labelText: 'Confirmer le mot de passe',
                            border: OutlineInputBorder(),
                          ),
                          obscureText: true,
                          validator: (value) =>
                              value != _passwordController.text
                                  ? 'Les mots de passe ne correspondent pas.'
                                  : null,
                        ),
                        if (_errorMessage != null) ...[
                          const SizedBox(height: 16),
                          Semantics(
                            liveRegion: true,
                            child: Text(
                              _errorMessage!,
                              style: TextStyle(
                                color: Theme.of(context).colorScheme.error,
                              ),
                            ),
                          ),
                        ],
                        const SizedBox(height: 24),
                        FilledButton(
                          onPressed: _isSubmitting ? null : _register,
                          child: _isSubmitting
                              ? const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Text('Créer mon compte'),
                        ),
                        TextButton(
                          onPressed: () => context.go('/login'),
                          child: const Text('Déjà un compte ? Se connecter'),
                        ),
                      ],
                    ),
                  ),
          ),
        ),
      ),
    );
  }
}
