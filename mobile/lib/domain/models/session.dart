class Session {
  const Session({
    required this.id,
    required this.type,
    required this.deadlineUtc,
    required this.status,
  });

  final int id;
  final String type;
  final DateTime deadlineUtc;
  final String status;

  factory Session.fromJson(Map<String, dynamic> json) {
    return Session(
      id: json['id'] as int,
      type: json['type'] as String,
      deadlineUtc: DateTime.parse(json['deadline_utc'] as String),
      status: json['status'] as String,
    );
  }
}
