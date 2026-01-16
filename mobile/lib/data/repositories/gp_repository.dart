import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:paddock/data/api_client.dart';
import 'package:paddock/data/api_exception.dart';
import 'package:paddock/domain/models/grand_prix.dart';
import 'package:paddock/domain/models/grand_prix_detail.dart';
import 'package:paddock/domain/models/season.dart';

class GpRepository {
  GpRepository(this._client);

  final ApiClient _client;

  Future<Season> fetchCurrentSeason() async {
    final response = await _client.get('/seasons/current');
    if (response.statusCode != 200) {
      throw ApiException.fromResponse(response);
    }
    return Season.fromJson(decodeJson(response.body));
  }

  Future<List<GrandPrix>> fetchGrandPrix(int seasonYear) async {
    final response = await _client.get('/gps?season_year=$seasonYear');
    if (response.statusCode != 200) {
      throw ApiException.fromResponse(response);
    }
    final data = decodeJsonList(response.body);
    return data.map((item) => GrandPrix.fromJson(item as Map<String, dynamic>)).toList();
  }

  Future<GrandPrixDetail> fetchGrandPrixDetail(int gpId) async {
    final response = await _client.get('/gps/$gpId');
    if (response.statusCode != 200) {
      throw ApiException.fromResponse(response);
    }
    return GrandPrixDetail.fromJson(decodeJson(response.body));
  }
}

final gpRepositoryProvider = Provider<GpRepository>((ref) {
  final client = ref.watch(apiClientProvider);
  return GpRepository(client);
});
