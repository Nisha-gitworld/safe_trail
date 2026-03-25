import 'package:flutter/material.dart';

/// Reusable danger score ring widget used on the home dashboard.
class DangerScoreRing extends StatelessWidget {
  final double score;
  final String zoneType;
  final double size;

  const DangerScoreRing({
    super.key,
    required this.score,
    required this.zoneType,
    this.size = 140,
  });

  Color get _color {
    if (score < 40) return const Color(0xFF639922);
    if (score < 70) return const Color(0xFFBA7517);
    return const Color(0xFFE24B4A);
  }

  String get _label => zoneType.toUpperCase();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: Stack(alignment: Alignment.center, children: [
        // Background ring
        CircularProgressIndicator(
          value: 1.0,
          strokeWidth: size * 0.07,
          color: _color.withOpacity(0.12),
        ),
        // Score ring
        CircularProgressIndicator(
          value: score / 100,
          strokeWidth: size * 0.07,
          color: _color,
          strokeCap: StrokeCap.round,
        ),
        // Centre content
        Column(mainAxisSize: MainAxisSize.min, children: [
          Text(
            score.round().toString(),
            style: TextStyle(
              fontSize: size * 0.26,
              fontWeight: FontWeight.w700,
              color: _color,
            ),
          ),
          Text(
            _label,
            style: TextStyle(
              fontSize: size * 0.09,
              fontWeight: FontWeight.w600,
              color: _color,
            ),
          ),
        ]),
      ]),
    );
  }
}


/// Compact inline risk badge (for list items, map popups)
class RiskBadge extends StatelessWidget {
  final double score;
  const RiskBadge({super.key, required this.score});

  Color get _bg {
    if (score < 40) return const Color(0xFFEAF3DE);
    if (score < 70) return const Color(0xFFFAEEDA);
    return const Color(0xFFFCEBEB);
  }

  Color get _fg {
    if (score < 40) return const Color(0xFF27500A);
    if (score < 70) return const Color(0xFF633806);
    return const Color(0xFF501313);
  }

  String get _text {
    if (score < 40) return 'Safe';
    if (score < 70) return 'Caution';
    return 'Danger';
  }

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
    decoration: BoxDecoration(color: _bg, borderRadius: BorderRadius.circular(20)),
    child: Text(_text, style: TextStyle(color: _fg, fontSize: 12, fontWeight: FontWeight.w600)),
  );
}


/// Alert severity chip
class AlertChip extends StatelessWidget {
  final int level;
  const AlertChip({super.key, required this.level});

  @override
  Widget build(BuildContext context) {
    final labels = ['None', 'Push', 'SMS', 'SOS'];
    final colors = [
      const Color(0xFF97C459), const Color(0xFFFAC775),
      const Color(0xFFE24B4A), const Color(0xFFA32D2D),
    ];
    final l = level.clamp(0, 3);
    return Chip(
      backgroundColor: colors[l].withOpacity(0.15),
      label: Text('Alert: ${labels[l]}',
          style: TextStyle(color: colors[l], fontSize: 11, fontWeight: FontWeight.w600)),
      padding: EdgeInsets.zero,
      visualDensity: VisualDensity.compact,
    );
  }
}
