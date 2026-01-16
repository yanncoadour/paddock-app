import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;

import 'package:paddock/core/config.dart';
import 'package:paddock/data/storage/token_storage.dart';
import 'package:paddock/presentation/providers.dart';

class ApiClient {
  ApiClient(this._ref, this._client, this._baseUrl, this._tokenStorage);

  final Ref _ref;
  final http.Client _client;
  final String _baseUrl;
  final TokenStorage _tokenStorage;

  Future<http.Response> get(String path) async {
    final uri = Uri.parse('$_baseUrl$path');
    final headers = await _buildHeaders();
    final response = await _client.get(uri, headers: headers);
    await _handleUnauthorized(response);
    return response;
  }

  Future<http.Response> post(String path, {Object? body}) async {
    final uri = Uri.parse('$_baseUrl$path');
    final headers = await _buildHeaders();
    final response = await _client.post(uri, headers: headers, body: body);
    await _handleUnauthorized(response);
    return response;
  }

  Future<Map<String, String>> _buildHeaders() async {
    final token = await _tokenStorage.readToken();
    final headers = <String, String>{
      'Content-Type': 'application/json',
    };
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  Future<void> _handleUnauthorized(http.Response response) async {
    if (response.statusCode == 401) {
      await _tokenStorage.clearToken();
      _ref.read(authControllerProvider.notifier).reset();
    }
  }
}

final httpClientProvider = Provider<http.Client>((ref) => http.Client());

final apiClientProvider = Provider<ApiClient>((ref) {
  final config = ref.watch(appConfigProvider);
  final client = ref.watch(httpClientProvider);
  final tokenStorage = ref.watch(tokenStorageProvider);
  return ApiClient(ref, client, config.baseUrl, tokenStorage);
});

Map<String, dynamic> decodeJson(String body) {
  return json.decode(body) as Map<String, dynamic>;
}

List<dynamic> decodeJsonList(String body) {
  return json.decode(body) as List<dynamic>;
}
