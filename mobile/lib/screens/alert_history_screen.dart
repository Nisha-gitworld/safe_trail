import 'package:flutter/material.dart';

class AlertHistoryScreen extends StatelessWidget {
  const AlertHistoryScreen({super.key});

  // Mock alert history — replace with ApiService.listIncidents()
  static const _alerts = [
    {
      "id": "INC-001",
      "type": "THEFT",
      "zone": "Dharavi Area",
      "time": "Yesterday 23:14",
      "status": "resolved",
      "desc": "Wallet snatched near market entrance",
    },
    {
      "id": "INC-002",
      "type": "ZONE_ALERT",
      "zone": "Kurla Station",
      "time": "2 days ago 21:08",
      "status": "auto",
      "desc": "Entered caution zone — moved to safety",
    },
    {
      "id": "INC-003",
      "type": "BUDDY",
      "zone": "Colaba",
      "time": "3 days ago 15:33",
      "status": "resolved",
      "desc": "Group member separated by 340m — rejoined",
    },
  ];

  Color _typeColor(String type) {
    switch (type) {
      case 'THEFT':      return const Color(0xFFF09595);
      case 'MEDICAL':    return const Color(0xFFE24B4A);
      case 'ZONE_ALERT': return const Color(0xFFFAC775);
      case 'BUDDY':      return const Color(0xFFB5D4F4);
      default:           return const Color(0xFFD3D1C7);
    }
  }

  IconData _typeIcon(String type) {
    switch (type) {
      case 'THEFT':      return Icons.no_backpack;
      case 'MEDICAL':    return Icons.local_hospital;
      case 'ZONE_ALERT': return Icons.location_off;
      case 'BUDDY':      return Icons.group_off;
      default:           return Icons.info_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Alert History', style: TextStyle(fontWeight: FontWeight.w600)),
      ),
      body: _alerts.isEmpty
          ? Center(
              child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                Icon(Icons.check_circle_outline, size: 64, color: Colors.grey[300]),
                const SizedBox(height: 12),
                Text('No alerts yet', style: TextStyle(color: Colors.grey[500], fontSize: 16)),
              ]),
            )
          : ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: _alerts.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (context, i) {
                final a = _alerts[i];
                final color = _typeColor(a['type']!);
                return Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: color.withOpacity(0.3)),
                  ),
                  child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: color.withOpacity(0.18),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Icon(_typeIcon(a['type']!), size: 20, color: color),
                    ),
                    const SizedBox(width: 12),
                    Expanded(child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(a['type']!.replaceAll('_', ' '),
                                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: a['status'] == 'resolved'
                                    ? const Color(0xFFEAF3DE) : const Color(0xFFFAEEDA),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Text(a['status']!,
                                  style: TextStyle(
                                    fontSize: 11,
                                    color: a['status'] == 'resolved'
                                        ? const Color(0xFF27500A) : const Color(0xFF633806),
                                  )),
                            ),
                          ],
                        ),
                        const SizedBox(height: 2),
                        Text(a['zone']!,
                            style: TextStyle(color: Colors.grey[600], fontSize: 12)),
                        const SizedBox(height: 4),
                        Text(a['desc']!,
                            style: const TextStyle(fontSize: 13)),
                        const SizedBox(height: 4),
                        Text(a['time']!,
                            style: TextStyle(color: Colors.grey[500], fontSize: 11)),
                      ],
                    )),
                  ]),
                );
              },
            ),
    );
  }
}
