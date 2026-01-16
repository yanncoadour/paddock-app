class Paddock {
  const Paddock({
    required this.id,
    required this.name,
    required this.joinCode,
    required this.seasonYear,
    required this.status,
    required this.role,
  });

  final int id;
  final String name;
  final String joinCode;
  final int seasonYear;
  final String status;
  final String role;

  factory Paddock.fromJson(Map<String, dynamic> json) {
    return Paddock(
      id: json['id'] as int,
      name: json['name'] as String,
      joinCode: json['join_code'] as String,
      seasonYear: json['season_year'] as int,
      status: json['status'] as String,
      role: json['role'] as String,
    );
  }
}
