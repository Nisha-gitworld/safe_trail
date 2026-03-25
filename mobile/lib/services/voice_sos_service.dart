import 'dart:async';
import 'dart:io';
import 'package:record/record.dart';
import 'package:permission_handler/permission_handler.dart';
import 'api_service.dart';
import 'location_service.dart';

/// Voice-triggered SOS service.
///
/// Listens for the keyword "help" in audio and automatically
/// triggers the SOS pipeline without the user needing to touch
/// the screen — critical for hands-free emergencies.
class VoiceSosService {
  final AudioRecorder _recorder = AudioRecorder();
  Timer?  _keywordCheckTimer;
  bool    _listening = false;
  bool    _triggered = false;
  String? _recordingPath;

  /// Keywords that trigger SOS in any language via Whisper
  static const _sosKeywords = [
    'help',  'ayuda', 'hilfe', 'aide',   'socorro',  // EN/ES/DE/FR/PT
    'bachao', 'madad', 'pomoc', 'soutez', 'tulong',  // HI/UR/PL/CZ/TL
    'emergency', 'sos', 'rescue',
  ];

  /// Start passive voice monitoring.
  /// Captures audio in 10-second chunks and sends each to the backend
  /// for keyword detection via Whisper.
  Future<void> startListening({
    required void Function(String transcript) onTriggered,
    required void Function(String error)      onError,
  }) async {
    if (_listening) return;

    // Request microphone permission
    final status = await Permission.microphone.request();
    if (!status.isGranted) {
      onError('Microphone permission denied');
      return;
    }

    _listening  = true;
    _triggered  = false;

    // Record in rolling 10-second chunks
    _keywordCheckTimer = Timer.periodic(const Duration(seconds: 10), (_) async {
      if (!_listening || _triggered) return;
      await _captureAndCheck(onTriggered: onTriggered, onError: onError);
    });

    // Start first recording immediately
    await _startChunkRecording();
  }

  Future<void> _startChunkRecording() async {
    final dir  = Directory.systemTemp;
    _recordingPath = '${dir.path}/sos_chunk_${DateTime.now().millisecondsSinceEpoch}.m4a';
    await _recorder.start(
      const RecordConfig(encoder: AudioEncoder.aacLc, bitRate: 32000),
      path: _recordingPath!,
    );
  }

  Future<void> _captureAndCheck({
    required void Function(String) onTriggered,
    required void Function(String) onError,
  }) async {
    try {
      // Stop current recording
      await _recorder.stop();
      final chunkPath = _recordingPath;

      // Start next chunk immediately (overlap)
      await _startChunkRecording();

      if (chunkPath == null) return;

      // Send audio to backend for transcription
      final file = File(chunkPath);
      if (!file.existsSync() || file.lengthSync() < 1000) return;

      final transcript = await ApiService.transcribeVoice(file.readAsBytesSync());
      if (transcript.isEmpty) return;

      // Keyword check (local — no round trip needed)
      final lower = transcript.toLowerCase();
      final matched = _sosKeywords.any((kw) => lower.contains(kw));

      if (matched && !_triggered) {
        _triggered = true;
        onTriggered(transcript);

        // Automatically dispatch SOS
        final pos = await LocationService.getCurrentPosition();
        await ApiService.triggerSOS(
          lat: pos.latitude,
          lng: pos.longitude,
          incidentType: 'ACCIDENT',
          description: 'Voice SOS: "$transcript"',
        );
      }

      // Clean up chunk file
      file.deleteSync();
    } catch (e) {
      onError('Voice SOS error: $e');
    }
  }

  Future<void> stopListening() async {
    _listening = false;
    _keywordCheckTimer?.cancel();
    if (await _recorder.isRecording()) {
      await _recorder.stop();
    }
  }

  bool get isListening => _listening;
  bool get wasTriggered => _triggered;

  void resetTrigger() => _triggered = false;

  void dispose() {
    _keywordCheckTimer?.cancel();
    _recorder.dispose();
  }
}

final voiceSosService = VoiceSosService();
