import 'dart:convert';

import 'package:paddock/data/api_client.dart';
import 'package:paddock/data/api_exception.dart';
import 'package:paddock/data/storage/token_storage.dart';
import 'package:paddock/domain/models/user.dart';

class AuthRepository {
  AuthRepository(this._client, this._tokenStorage);

  final ApiClient _client;
  final TokenStorage _tokenStorage;

  Future<void> register({
    required String email,
    required String password,
    required String displayName,
  }) async {
    final response = await _client.post(
      '/auth/register',
      body: json.encode({
        'email': email,
        'password': password,
        'display_name': displayName,
      }),
    );

    if (response.statusCode != 200) {
      throw ApiException.fromResponse(response);
    }

    final token = decodeJson(response.body)['access_token'] as String;
    await _tokenStorage.writeToken(token);
  }

  Future<void> login({
    required String email,
    required String password,
  }) async {
    final response = await _client.post(
      '/auth/login',
      body: json.encode({
        'email': email,
        'password': password,
      }),
    );

    if (response.statusCode != 200) {
      throw ApiException.fromResponse(response);
    }

    final token = decodeJson(response.body)['access_token'] as String;
    await _tokenStorage.writeToken(token);
  }

  Future<User> fetchMe() async {
    final response = await _client.get('/me');
    if (response.statusCode != 200) {
      throw ApiException.fromResponse(response);
    }
    return User.fromJson(decodeJson(response.body));
  }

  Future<void> logout() async {
    await _tokenStorage.clearToken();
  }
}
