class Season {
  const Season({
    required this.id,
    required this.year,
    required this.name,
    required this.timezoneDisplay,
  });

  final int id;
  final int year;
  final String name;
  final String timezoneDisplay;

  factory Season.fromJson(Map<String, dynamic> json) {
    return Season(
      id: json['id'] as int,
      year: json['year'] as int,
      name: json['name'] as String,
      timezoneDisplay: json['timezone_display'] as String,
    );
  }
}
