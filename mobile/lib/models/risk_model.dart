class RiskResponse {
  final double dangerScore;
  final String zoneType;
  final int    alertLevel;
  final String recommendation;

  RiskResponse({
    required this.dangerScore,
    required this.zoneType,
    required this.alertLevel,
    required this.recommendation,
  });

  factory RiskResponse.fromJson(Map<String, dynamic> json) => RiskResponse(
    dangerScore:    (json['danger_score'] as num).toDouble(),
    zoneType:       json['zone_type'] as String,
    alertLevel:     json['alert_level'] as int,
    recommendation: json['recommendation'] as String,
  );
}
