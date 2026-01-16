class GrandPrix {
  const GrandPrix({
    required this.id,
    required this.seasonId,
    required this.name,
    required this.country,
    required this.startsAtUtc,
    required this.hasSprint,
    required this.roundNumber,
  });

  final int id;
  final int seasonId;
  final String name;
  final String country;
  final DateTime startsAtUtc;
  final bool hasSprint;
  final int roundNumber;

  factory GrandPrix.fromJson(Map<String, dynamic> json) {
    return GrandPrix(
      id: json['id'] as int,
      seasonId: json['season_id'] as int,
      name: json['name'] as String,
      country: json['country'] as String,
      startsAtUtc: DateTime.parse(json['starts_at_utc'] as String),
      hasSprint: json['has_sprint'] as bool,
      roundNumber: json['round_number'] as int,
    );
  }
}
