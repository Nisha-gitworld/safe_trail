import 'package:flutter/material.dart';
import '../services/api_service.dart';

class BuddyScreen extends StatefulWidget {
  const BuddyScreen({super.key});
  @override
  State<BuddyScreen> createState() => _BuddyScreenState();
}

class _BuddyScreenState extends State<BuddyScreen> {
  final _codeController = TextEditingController();
  String? _groupId;
  Map<String, dynamic>? _groupStatus;
  bool _loading = false;

  Future<void> _joinGroup() async {
    final code = _codeController.text.trim().toUpperCase();
    if (code.isEmpty) return;
    setState(() => _loading = true);
    try {
      // ApiService.joinGroup(code) would call /api/buddy/groups/{id}/join
      setState(() { _groupId = code; _loading = false; });
      _refreshStatus();
    } catch (e) {
      setState(() => _loading = false);
      _showSnack('Could not join group: $e');
    }
  }

  Future<void> _refreshStatus() async {
    if (_groupId == null) return;
    setState(() => _loading = true);
    try {
      // Mock status for demo
      await Future.delayed(const Duration(milliseconds: 600));
      setState(() {
        _groupStatus = {
          "group_name":  "Mumbai Heritage Tour",
          "member_count": 6,
          "online_count": 5,
          "group_score":  34.0,
          "group_zone":   "safe",
          "members": [
            {"user_id": "u001", "online": true, "score": 22.0, "checkin_ok": true},
            {"user_id": "u002", "online": true, "score": 41.0, "checkin_ok": true},
            {"user_id": "u003", "online": true, "score": 18.0, "checkin_ok": true},
            {"user_id": "u004", "online": false,"score": 0.0,  "checkin_ok": false},
            {"user_id": "u005", "online": true, "score": 55.0, "checkin_ok": true},
            {"user_id": "me",   "online": true, "score": 29.0, "checkin_ok": true},
          ]
        };
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  Future<void> _checkIn() async {
    // ApiService.checkIn() → POST /api/buddy/checkin
    _showSnack('✅ Check-in recorded — next in 2 hours');
  }

  void _showSnack(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  Color _scoreColor(double score) {
    if (score < 40) return const Color(0xFF639922);
    if (score < 70) return const Color(0xFFBA7517);
    return const Color(0xFFE24B4A);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Buddy System', style: TextStyle(fontWeight: FontWeight.w600)),
        actions: [
          if (_groupId != null)
            IconButton(icon: const Icon(Icons.refresh), onPressed: _refreshStatus),
        ],
      ),
      body: _groupId == null ? _buildJoinView() : _buildGroupView(),
    );
  }

  Widget _buildJoinView() => Padding(
    padding: const EdgeInsets.all(24),
    child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      const SizedBox(height: 40),
      const Icon(Icons.group_rounded, size: 64, color: Color(0xFF534AB7)),
      const SizedBox(height: 20),
      const Text('Join your tour group', textAlign: TextAlign.center,
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
      const SizedBox(height: 8),
      Text('Your guide will share a group code', textAlign: TextAlign.center,
          style: TextStyle(color: Colors.grey[600])),
      const SizedBox(height: 40),
      TextField(
        controller: _codeController,
        decoration: InputDecoration(
          labelText: 'Group code (e.g. A3F2BC)',
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
          prefixIcon: const Icon(Icons.tag),
        ),
        textCapitalization: TextCapitalization.characters,
      ),
      const SizedBox(height: 16),
      FilledButton(
        onPressed: _loading ? null : _joinGroup,
        style: FilledButton.styleFrom(
          padding: const EdgeInsets.symmetric(vertical: 14),
          backgroundColor: const Color(0xFF534AB7),
        ),
        child: _loading
            ? const CircularProgressIndicator(color: Colors.white, strokeWidth: 2)
            : const Text('Join Group', style: TextStyle(fontSize: 16)),
      ),
    ]),
  );

  Widget _buildGroupView() {
    final gs = _groupStatus;
    if (gs == null) {
      return const Center(child: CircularProgressIndicator());
    }
    final zoneColor = gs['group_zone'] == 'safe'
        ? const Color(0xFF639922)
        : gs['group_zone'] == 'caution'
            ? const Color(0xFFBA7517)
            : const Color(0xFFE24B4A);
    final members = (gs['members'] as List).cast<Map<String, dynamic>>();

    return ListView(padding: const EdgeInsets.all(16), children: [
      // Group card
      Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: const Color(0xFF534AB7),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(children: [
          Text(gs['group_name'], style: const TextStyle(color: Colors.white,
              fontSize: 20, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Row(mainAxisAlignment: MainAxisAlignment.spaceAround, children: [
            _GroupStat('${gs['online_count']}/${gs['member_count']}', 'Online'),
            _GroupStat('${gs['group_score'].round()}', 'Group score'),
            _GroupStat(gs['group_zone'].toString().toUpperCase(), 'Zone'),
          ]),
        ]),
      ),
      const SizedBox(height: 12),

      // Check-in button
      OutlinedButton.icon(
        onPressed: _checkIn,
        icon: const Icon(Icons.check_circle_outline),
        label: const Text("I'm safe — check in"),
        style: OutlinedButton.styleFrom(
          padding: const EdgeInsets.symmetric(vertical: 12),
        ),
      ),
      const SizedBox(height: 16),

      // Member list
      const Text('Group members', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
      const SizedBox(height: 8),
      ...members.map((m) => Card(
        margin: const EdgeInsets.only(bottom: 8),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        child: ListTile(
          leading: CircleAvatar(
            backgroundColor: m['online'] == true
                ? _scoreColor((m['score'] as num).toDouble()).withOpacity(0.15)
                : Colors.grey[200],
            child: Icon(
              m['online'] == true ? Icons.person : Icons.person_off,
              color: m['online'] == true
                  ? _scoreColor((m['score'] as num).toDouble())
                  : Colors.grey,
              size: 20,
            ),
          ),
          title: Text(
            m['user_id'] == 'me' ? 'You' : 'Member ${m['user_id']}',
            style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 14),
          ),
          subtitle: Text(
            m['online'] == true ? 'Score: ${(m['score'] as num).round()}' : 'Offline',
            style: TextStyle(fontSize: 12, color: Colors.grey[600]),
          ),
          trailing: m['checkin_ok'] == false
              ? const Icon(Icons.warning_amber, color: Color(0xFFE24B4A), size: 20)
              : const Icon(Icons.check_circle, color: Color(0xFF639922), size: 20),
        ),
      )),
    ]);
  }
}

class _GroupStat extends StatelessWidget {
  final String value, label;
  const _GroupStat(this.value, this.label);

  @override
  Widget build(BuildContext context) => Column(children: [
    Text(value, style: const TextStyle(color: Colors.white, fontSize: 22,
        fontWeight: FontWeight.w600)),
    Text(label, style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 12)),
  ]);
}
