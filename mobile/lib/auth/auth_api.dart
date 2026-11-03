import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

class AuthApiException implements Exception {
  const AuthApiException(this.message);

  final String message;

  @override
  String toString() => message;
}

class AuthApi {
  AuthApi({
    http.Client? client,
    FlutterSecureStorage? storage,
    String? baseUrl,
  }) : _client = client ?? http.Client(),
       _storage = storage ?? const FlutterSecureStorage(),
       _baseUrl = baseUrl ?? _defaultBaseUrl;

  static const _accessTokenKey = 'health_v1_access_token';
  static const _refreshTokenKey = 'health_v1_refresh_token';
  static const _configuredUrl = String.fromEnvironment('API_BASE_URL');

  static String get _defaultBaseUrl {
    if (_configuredUrl.isNotEmpty) {
      return _configuredUrl;
    }
    if (kIsWeb || defaultTargetPlatform == TargetPlatform.iOS) {
      return 'http://localhost:8000';
    }
    return 'http://10.0.2.2:8000';
  }

  static final instance = AuthApi();

  final http.Client _client;
  final FlutterSecureStorage _storage;
  final String _baseUrl;

  Future<String> login(String email, String password) async {
    final response = await _post(
      '/auth/login',
      {'email': email.trim(), 'password': password},
    );
    if (response.statusCode != 200) {
      throw AuthApiException(_errorMessage(response));
    }

    final body = _decodeResponse(response);
    final accessToken = body['access_token'];
    final refreshToken = body['refresh_token'];
    if (accessToken is! String || refreshToken is! String) {
      throw const AuthApiException('La réponse de connexion ne contient pas les jetons.');
    }

    await _saveTokens(accessToken, refreshToken);
    final user = body['user'];
    return user is Map<String, dynamic> && user['email'] is String
        ? user['email'] as String
        : email.trim();
  }

  Future<void> refresh() async {
    final refreshToken = await _storage.read(key: _refreshTokenKey);
    if (refreshToken == null) {
      throw const AuthApiException('Aucune session à renouveler. Connectez-vous à nouveau.');
    }

    final response = await _post('/auth/refresh', {'refresh_token': refreshToken});
    if (response.statusCode == 401) {
      await clearTokens();
      throw const AuthApiException('Votre session a expiré. Connectez-vous à nouveau.');
    }
    if (response.statusCode != 200) {
      throw AuthApiException(_errorMessage(response));
    }

    final body = _decodeResponse(response);
    final accessToken = body['access_token'];
    final nextRefreshToken = body['refresh_token'];
    if (accessToken is! String || nextRefreshToken is! String) {
      throw const AuthApiException('La réponse de renouvellement ne contient pas les jetons.');
    }
    await _saveTokens(accessToken, nextRefreshToken);
  }

  Future<String> currentUserEmail() async {
    final accessToken = await _storage.read(key: _accessTokenKey);
    if (accessToken == null) {
      throw const AuthApiException('Aucune session. Connectez-vous à nouveau.');
    }

    var response = await _getCurrentUser(accessToken);
    if (response.statusCode == 401) {
      await refresh();
      final refreshedAccessToken = await _storage.read(key: _accessTokenKey);
      if (refreshedAccessToken == null) {
        throw const AuthApiException('Votre session a expiré. Connectez-vous à nouveau.');
      }
      response = await _getCurrentUser(refreshedAccessToken);
    }
    if (response.statusCode == 401) {
      await clearTokens();
      throw const AuthApiException('Votre session a expiré. Connectez-vous à nouveau.');
    }
    if (response.statusCode != 200) {
      throw AuthApiException(_errorMessage(response));
    }

    final body = _decodeResponse(response);
    final email = body['email'];
    if (email is! String) {
      throw const AuthApiException('La réponse utilisateur est invalide.');
    }
    return email;
  }

  Future<void> logout() async {
    final refreshToken = await _storage.read(key: _refreshTokenKey);
    if (refreshToken == null) {
      return;
    }

    final response = await _post('/auth/logout', {'refresh_token': refreshToken});
    if (response.statusCode != 204 && response.statusCode != 401) {
      throw AuthApiException(_errorMessage(response));
    }
    await clearTokens();
  }

  Future<void> clearTokens() async {
    await _storage.delete(key: _accessTokenKey);
    await _storage.delete(key: _refreshTokenKey);
  }

  Future<http.Response> _post(String path, Map<String, Object?> body) async {
    try {
      return await _client
          .post(
            Uri.parse('$_baseUrl$path'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 10));
    } on http.ClientException {
      throw const AuthApiException('Impossible de joindre le serveur.');
    } on TimeoutException {
      throw const AuthApiException('Le serveur met trop de temps à répondre.');
    }
  }

  Future<http.Response> _getCurrentUser(String accessToken) async {
    try {
      return await _client
          .get(
            Uri.parse('$_baseUrl/auth/me'),
            headers: {'Authorization': 'Bearer $accessToken'},
          )
          .timeout(const Duration(seconds: 10));
    } on http.ClientException {
      throw const AuthApiException('Impossible de joindre le serveur.');
    } on TimeoutException {
      throw const AuthApiException('Le serveur met trop de temps à répondre.');
    }
  }

  Future<void> _saveTokens(String accessToken, String refreshToken) async {
    await _storage.write(key: _accessTokenKey, value: accessToken);
    await _storage.write(key: _refreshTokenKey, value: refreshToken);
  }

  Map<String, dynamic> _decodeResponse(http.Response response) {
    final Object? body;
    try {
      body = jsonDecode(response.body);
    } on FormatException {
      throw const AuthApiException('Le serveur a renvoyé une réponse invalide.');
    }
    if (body is! Map<String, dynamic>) {
      throw const AuthApiException('Le serveur a renvoyé une réponse invalide.');
    }
    return body;
  }

  String _errorMessage(http.Response response) {
    try {
      final body = _decodeResponse(response);
      final detail = body['detail'];
      if (detail is String) {
        return detail;
      }
    } on FormatException {
      return 'Le serveur a renvoyé une réponse invalide.';
    }
    return 'La requête a échoué (${response.statusCode}).';
  }
}
