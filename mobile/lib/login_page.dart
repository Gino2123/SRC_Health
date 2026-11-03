import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'auth/auth_api.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isSubmitting = false;
  String? _errorMessage;
  String? _loggedInEmail;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    try {
      await AuthApi.instance.login(
        _emailController.text,
        _passwordController.text,
      );
      final email = await AuthApi.instance.currentUserEmail();
      if (mounted) {
        setState(() => _loggedInEmail = email);
      }
    } on AuthApiException catch (error) {
      if (mounted) {
        setState(() => _errorMessage = error.message);
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  Future<void> _logout() async {
    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });
    try {
      await AuthApi.instance.logout();
      if (mounted) {
        setState(() => _loggedInEmail = null);
      }
    } on AuthApiException catch (error) {
      if (mounted) {
        setState(() => _errorMessage = error.message);
      }
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
            child: _loggedInEmail != null
                ? Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Connecté en tant que $_loggedInEmail',
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      FilledButton(
                        onPressed: _isSubmitting ? null : _logout,
                        child: const Text('Se déconnecter'),
                      ),
                    ],
                  )
                : Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          'Connexion',
                          style: Theme.of(context).textTheme.headlineMedium,
                        ),
                        const SizedBox(height: 8),
                        const Text('Saisissez les identifiants de votre compte.'),
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
                            labelText: 'Mot de passe',
                            border: OutlineInputBorder(),
                          ),
                          obscureText: true,
                          maxLength: 128,
                          autofillHints: const [AutofillHints.password],
                          validator: (value) => value == null || value.isEmpty
                              ? 'Saisissez votre mot de passe.'
                              : null,
                        ),
                        if (_errorMessage != null) ...[
                          const SizedBox(height: 8),
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
                        const SizedBox(height: 16),
                        FilledButton(
                          onPressed: _isSubmitting ? null : _login,
                          child: _isSubmitting
                              ? const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Text('Se connecter'),
                        ),
                        TextButton(
                          onPressed: () => context.go('/'),
                          child: const Text('Créer un compte'),
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
