import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/api_service.dart';
import '../services/location_service.dart';

class SOSScreen extends StatefulWidget {
  const SOSScreen({super.key});
  @override
  State<SOSScreen> createState() => _SOSScreenState();
}

class _SOSScreenState extends State<SOSScreen> with TickerProviderStateMixin {
  bool _dispatched = false;
  bool _loading    = false;
  String _status   = 'Hold button for 2 seconds to trigger SOS';
  late AnimationController _pulseCtrl;
  late Animation<double>   _pulseAnim;

  @override
  void initState() {
    super.initState();
    _pulseCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 900))
      ..repeat(reverse: true);
    _pulseAnim = Tween<double>(begin: 1.0, end: 1.08).animate(
      CurvedAnimation(parent: _pulseCtrl, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _pulseCtrl.dispose();
    super.dispose();
  }

  Future<void> _triggerSOS() async {
    if (_dispatched || _loading) return;
    HapticFeedback.heavyImpact();
    setState(() { _loading = true; _status = 'Getting your location…'; });

    try {
      final pos = await LocationService.getCurrentPosition();
      setState(() => _status = 'Dispatching emergency services…');
      await ApiService.triggerSOS(lat: pos.latitude, lng: pos.longitude);
      HapticFeedback.heavyImpact();
      setState(() {
        _dispatched = true;
        _loading    = false;
        _status     = 'Emergency services notified!';
      });
    } catch (e) {
      setState(() { _loading = false; _status = 'Error: ${e.toString()}. Try again.'; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _dispatched ? const Color(0xFFFCEBEB) : null,
      appBar: AppBar(
        backgroundColor: const Color(0xFFA32D2D),
        foregroundColor: Colors.white,
        title: const Text('Emergency SOS', style: TextStyle(fontWeight: FontWeight.w600)),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(children: [
            // Status banner
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 16),
              decoration: BoxDecoration(
                color: _dispatched ? const Color(0xFFE24B4A).withOpacity(0.12) : Colors.grey[100],
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: _dispatched ? const Color(0xFFE24B4A) : Colors.grey[300]!),
              ),
              child: Text(_status,
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: _dispatched ? const Color(0xFFA32D2D) : Colors.grey[700],
                  fontWeight: FontWeight.w500,
                )),
            ),
            const Spacer(),

            // SOS Button
            GestureDetector(
              onLongPress: _triggerSOS,
              child: ScaleTransition(
                scale: _pulseAnim,
                child: Container(
                  width: 180, height: 180,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: const Color(0xFFE24B4A),
                    boxShadow: [BoxShadow(
                      color: const Color(0xFFE24B4A).withOpacity(0.35),
                      blurRadius: 40, spreadRadius: 10,
                    )],
                  ),
                  child: _loading
                      ? const CircularProgressIndicator(color: Colors.white, strokeWidth: 3)
                      : Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                          Icon(_dispatched ? Icons.check_circle : Icons.sos_rounded,
                              color: Colors.white, size: 56),
                          const SizedBox(height: 6),
                          Text(_dispatched ? 'SENT' : 'SOS',
                              style: const TextStyle(color: Colors.white, fontSize: 22,
                                  fontWeight: FontWeight.w700)),
                        ]),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text('Hold for 2 seconds', style: TextStyle(color: Colors.grey[500], fontSize: 13)),

            const Spacer(),

            // Status checklist
            _StatusRow(label: 'Location sharing', active: true),
            _StatusRow(label: 'Digital ID attached', active: true),
            _StatusRow(label: 'Authorities notified', active: _dispatched),
            _StatusRow(label: 'Emergency contact alerted', active: _dispatched),

            const SizedBox(height: 24),

            // Voice SOS note
            Container(
              padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 14),
              decoration: BoxDecoration(
                color: const Color(0xFFEEEDFE),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Row(children: [
                const Icon(Icons.mic, color: Color(0xFF534AB7), size: 18),
                const SizedBox(width: 8),
                Expanded(child: Text(
                  '"Help!" voice trigger is active — shout to trigger SOS hands-free',
                  style: TextStyle(color: const Color(0xFF26215C), fontSize: 12),
                )),
              ]),
            ),
          ]),
        ),
      ),
    );
  }
}

class _StatusRow extends StatelessWidget {
  final String label;
  final bool   active;
  const _StatusRow({required this.label, required this.active});

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 5),
    child: Row(children: [
      Icon(active ? Icons.check_circle : Icons.radio_button_unchecked,
          color: active ? const Color(0xFF639922) : Colors.grey[400], size: 20),
      const SizedBox(width: 10),
      Text(label, style: TextStyle(
        color: active ? Colors.grey[800] : Colors.grey[500],
        fontWeight: active ? FontWeight.w500 : FontWeight.normal,
      )),
    ]),
  );
}
