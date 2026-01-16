class Standing {
  const Standing({
    required this.userId,
    required this.rank,
    required this.points,
  });

  final int userId;
  final int rank;
  final double points;

  factory Standing.fromJson(Map<String, dynamic> json) {
    final pointsValue = json['points'] ?? json['points_total'];
    return Standing(
      userId: json['user_id'] as int,
      rank: json['rank'] as int,
      points: (pointsValue as num).toDouble(),
    );
  }
}
