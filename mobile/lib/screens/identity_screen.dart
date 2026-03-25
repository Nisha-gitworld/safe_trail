import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';

class IdentityScreen extends StatelessWidget {
  const IdentityScreen({super.key});

  static const _did = 'did:polygon:0x8f3a...4d2c';
  static const _qrData = 'https://safetrail.app/verify?did=0x8f3a4d2c';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Digital Identity', style: TextStyle(fontWeight: FontWeight.w600)),
        actions: [
          IconButton(icon: const Icon(Icons.share_outlined), onPressed: () {}),
        ],
      ),
      body: ListView(padding: const EdgeInsets.all(20), children: [
        // Avatar + Name Card
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF534AB7), Color(0xFF7F77DD)],
              begin: Alignment.topLeft, end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Column(children: [
            CircleAvatar(
              radius: 40,
              backgroundColor: Colors.white.withOpacity(0.2),
              child: const Text('AK', style: TextStyle(fontSize: 28, color: Colors.white, fontWeight: FontWeight.w600)),
            ),
            const SizedBox(height: 12),
            const Text('Arjun Kumar', style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            Text('India · Expires 2027', style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 14)),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.15),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                const Icon(Icons.verified, color: Colors.white, size: 16),
                const SizedBox(width: 6),
                Text('DID Registered · Polygon', style: TextStyle(color: Colors.white.withOpacity(0.9), fontSize: 12)),
              ]),
            ),
          ]),
        ),
        const SizedBox(height: 20),

        // QR Code
        Card(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          elevation: 0,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(children: [
              const Text('Emergency QR Code', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
              const SizedBox(height: 4),
              Text('Scan to verify identity during emergency', style: TextStyle(color: Colors.grey[600], fontSize: 12)),
              const SizedBox(height: 16),
              QrImageView(data: _qrData, version: QrVersions.auto, size: 160),
              const SizedBox(height: 12),
              Text(_did, style: TextStyle(fontSize: 11, color: Colors.grey[500], fontFamily: 'monospace')),
            ]),
          ),
        ),
        const SizedBox(height: 16),

        // Encrypted attributes
        const Text('Stored Attributes (Emergency Access Only)',
            style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
        const SizedBox(height: 10),
        _EncryptedField(icon: Icons.water_drop, label: 'Blood Type', value: 'O+'),
        _EncryptedField(icon: Icons.flag, label: 'Nationality', value: 'Indian'),
        _EncryptedField(icon: Icons.phone, label: 'Embassy Contact', value: '+91-11-2301-4000'),
        _EncryptedField(icon: Icons.warning_amber, label: 'Allergies', value: 'Penicillin'),
        _EncryptedField(icon: Icons.contact_emergency, label: 'Emergency Contact', value: '+91-98765-43210'),

        const SizedBox(height: 20),

        // IPFS info
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: const Color(0xFFE1F5EE),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(children: [
            const Icon(Icons.lock, color: Color(0xFF085041), size: 18),
            const SizedBox(width: 10),
            Expanded(child: Text(
              'Your data is encrypted with AES-256 and stored on IPFS. Only the content hash is on-chain.',
              style: TextStyle(fontSize: 12, color: const Color(0xFF0F6E56)),
            )),
          ]),
        ),
      ]),
    );
  }
}

class _EncryptedField extends StatelessWidget {
  final IconData icon;
  final String   label, value;
  const _EncryptedField({required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(bottom: 8),
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
    decoration: BoxDecoration(
      color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.3),
      borderRadius: BorderRadius.circular(10),
    ),
    child: Row(children: [
      Icon(icon, size: 18, color: const Color(0xFF534AB7)),
      const SizedBox(width: 12),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label, style: TextStyle(fontSize: 11, color: Colors.grey[600])),
        Text(value,  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500)),
      ])),
      const Icon(Icons.lock_outline, size: 16, color: Colors.grey),
    ]),
  );
}
