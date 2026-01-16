import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class TokenStorage {
  static const _key = 'auth_token';
  final FlutterSecureStorage _storage;

  const TokenStorage(this._storage);

  Future<String?> readToken() => _storage.read(key: _key);

  Future<void> writeToken(String token) => _storage.write(key: _key, value: token);

  Future<void> clearToken() => _storage.delete(key: _key);
}
