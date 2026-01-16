import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:paddock/data/api_client.dart';
import 'package:paddock/data/api_exception.dart';
import 'package:paddock/domain/models/standing.dart';

class StandingsRepository {
  StandingsRepository(this._client);

  final ApiClient _client;

  Future<List<Standing>> fetchGpStandings(int gpId) async {
    final response = await _client.get('/standings/gp/$gpId');
    if (response.statusCode != 200) {
      throw ApiException.fromResponse(response);
    }
    final data = decodeJsonList(response.body);
    return data.map((item) => Standing.fromJson(item as Map<String, dynamic>)).toList();
  }

  Future<List<Standing>> fetchSeasonStandings({required int seasonId, required int paddockId}) async {
    final response = await _client.get('/standings/season/$seasonId?paddock_id=$paddockId');
    if (response.statusCode != 200) {
      throw ApiException.fromResponse(response);
    }
    final data = decodeJsonList(response.body);
    return data.map((item) => Standing.fromJson(item as Map<String, dynamic>)).toList();
  }
}

final standingsRepositoryProvider = Provider<StandingsRepository>((ref) {
  final client = ref.watch(apiClientProvider);
  return StandingsRepository(client);
});
