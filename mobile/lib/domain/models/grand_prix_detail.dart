import 'package:paddock/domain/models/grand_prix.dart';
import 'package:paddock/domain/models/session.dart';

class GrandPrixDetail extends GrandPrix {
  const GrandPrixDetail({
    required super.id,
    required super.seasonId,
    required super.name,
    required super.country,
    required super.startsAtUtc,
    required super.hasSprint,
    required super.roundNumber,
    required this.sessions,
  });

  final List<Session> sessions;

  factory GrandPrixDetail.fromJson(Map<String, dynamic> json) {
    return GrandPrixDetail(
      id: json['id'] as int,
      seasonId: json['season_id'] as int,
      name: json['name'] as String,
      country: json['country'] as String,
      startsAtUtc: DateTime.parse(json['starts_at_utc'] as String),
      hasSprint: json['has_sprint'] as bool,
      roundNumber: json['round_number'] as int,
      sessions: (json['sessions'] as List<dynamic>)
          .map((item) => Session.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}
