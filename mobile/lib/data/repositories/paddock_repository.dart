import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:paddock/data/api_client.dart';
import 'package:paddock/data/api_exception.dart';
import 'package:paddock/domain/models/paddock.dart';

class PaddockRepository {
  PaddockRepository(this._client);

  final ApiClient _client;

  Future<List<Paddock>> fetchPaddocks() async {
    final response = await _client.get('/paddocks');
    if (response.statusCode != 200) {
      throw ApiException.fromResponse(response);
    }
    final data = decodeJsonList(response.body);
    return data.map((item) => Paddock.fromJson(item as Map<String, dynamic>)).toList();
  }

  Future<Paddock> fetchPaddock(int paddockId) async {
    final response = await _client.get('/paddocks/$paddockId');
    if (response.statusCode != 200) {
      throw ApiException.fromResponse(response);
    }
    return Paddock.fromJson(decodeJson(response.body));
  }

  Future<Paddock> createPaddock({required String name, required int seasonYear}) async {
    final response = await _client.post(
      '/paddocks',
      body: json.encode({
        'name': name,
        'season_year': seasonYear,
      }),
    );
    if (response.statusCode != 200) {
      throw ApiException.fromResponse(response);
    }
    return Paddock.fromJson(decodeJson(response.body));
  }

  Future<Paddock> joinPaddock({required String joinCode}) async {
    final response = await _client.post(
      '/paddocks/join',
      body: json.encode({
        'join_code': joinCode,
      }),
    );
    if (response.statusCode != 200) {
      throw ApiException.fromResponse(response);
    }
    return Paddock.fromJson(decodeJson(response.body));
  }

  Future<Paddock> lockPaddock(int paddockId) async {
    final response = await _client.post('/paddocks/$paddockId/lock');
    if (response.statusCode != 200) {
      throw ApiException.fromResponse(response);
    }
    return Paddock.fromJson(decodeJson(response.body));
  }
}

final paddockRepositoryProvider = Provider<PaddockRepository>((ref) {
  final client = ref.watch(apiClientProvider);
  return PaddockRepository(client);
});
