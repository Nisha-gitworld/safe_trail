import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/location_service.dart';
import '../services/api_service.dart';
import '../models/risk_model.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});
  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  RiskResponse? _risk;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _startRiskPolling();
  }

  Future<void> _startRiskPolling() async {
    await _fetchRisk();
    // Poll every 10 seconds
    Future.delayed(const Duration(seconds: 10), _startRiskPolling);
  }

  Future<void> _fetchRisk() async {
    try {
      final pos  = await LocationService.getCurrentPosition();
      final risk = await ApiService.getRiskScore(
        lat: pos.latitude, lng: pos.longitude,
        hour: DateTime.now().hour,
      );
      if (mounted) setState(() { _risk = risk; _loading = false; });
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Color get _zoneColor {
    final score = _risk?.dangerScore ?? 0;
    if (score < 40) return const Color(0xFF639922);
    if (score < 70) return const Color(0xFFBA7517);
    return const Color(0xFFE24B4A);
  }

  String get _zoneLabel => _risk?.zoneType.toUpperCase() ?? 'LOADING';

  @override
  Widget build(BuildContext context) {
    final score = _risk?.dangerScore.round() ?? 0;

    return Scaffold(
      appBar: AppBar(
        title: const Row(children: [
          Icon(Icons.shield_rounded, color: Color(0xFF534AB7)),
          SizedBox(width: 8),
          Text('SafeTrail', style: TextStyle(fontWeight: FontWeight.w600)),
        ]),
        actions: [
          IconButton(icon: const Icon(Icons.notifications_outlined), onPressed: () {}),
          IconButton(icon: const Icon(Icons.settings_outlined), onPressed: () {}),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _fetchRisk,
              child: ListView(padding: const EdgeInsets.all(16), children: [
                // ── Danger Score Card ───────────────────────────────────────
                Card(
                  elevation: 0,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                  color: _zoneColor.withOpacity(0.08),
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(children: [
                      Text('Danger Score', style: TextStyle(color: Colors.grey[600], fontSize: 14)),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: 120, height: 120,
                        child: Stack(alignment: Alignment.center, children: [
                          CircularProgressIndicator(
                            value: score / 100,
                            strokeWidth: 10,
                            color: _zoneColor,
                            backgroundColor: _zoneColor.withOpacity(0.15),
                          ),
                          Column(mainAxisSize: MainAxisSize.min, children: [
                            Text('$score', style: TextStyle(fontSize: 36, fontWeight: FontWeight.w600, color: _zoneColor)),
                            Text(_zoneLabel, style: TextStyle(fontSize: 11, color: _zoneColor, fontWeight: FontWeight.w500)),
                          ]),
                        ]),
                      ),
                      const SizedBox(height: 12),
                      Text(_risk?.recommendation ?? '', textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.grey[700], fontSize: 13)),
                    ]),
                  ),
                ),
                const SizedBox(height: 16),

                // ── Stats Row ───────────────────────────────────────────────
                Row(children: [
                  _StatCard(label: 'Zone', value: _risk?.zoneType ?? '-', icon: Icons.location_on),
                  const SizedBox(width: 12),
                  _StatCard(label: 'Alert Level', value: 'Level ${_risk?.alertLevel ?? 0}', icon: Icons.warning_amber),
                  const SizedBox(width: 12),
                  _StatCard(label: 'DID', value: 'Active', icon: Icons.verified_user),
                ]),
                const SizedBox(height: 16),

                // ── Recent Alerts ───────────────────────────────────────────
                Text('Recent Alerts', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                const SizedBox(height: 8),
                _AlertTile(color: const Color(0xFFFAEEDA), icon: Icons.people, text: 'Market area: moderate crowd density'),
                _AlertTile(color: const Color(0xFFEAF3DE), icon: Icons.check_circle, text: 'Marine Drive: all clear'),
                _AlertTile(color: const Color(0xFFE6F1FB), icon: Icons.info, text: 'Your DID is registered and active'),
              ]),
            ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label, value;
  final IconData icon;
  const _StatCard({required this.label, required this.value, required this.icon});

  @override
  Widget build(BuildContext context) => Expanded(
    child: Card(
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.4),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
        child: Column(children: [
          Icon(icon, size: 20, color: Theme.of(context).colorScheme.primary),
          const SizedBox(height: 4),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
          Text(label, style: TextStyle(fontSize: 11, color: Colors.grey[600])),
        ]),
      ),
    ),
  );
}

class _AlertTile extends StatelessWidget {
  final Color color;
  final IconData icon;
  final String text;
  const _AlertTile({required this.color, required this.icon, required this.text});

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(bottom: 8),
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
    decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(10)),
    child: Row(children: [
      Icon(icon, size: 18, color: Colors.grey[700]),
      const SizedBox(width: 10),
      Expanded(child: Text(text, style: TextStyle(fontSize: 13, color: Colors.grey[800]))),
    ]),
  );
}
