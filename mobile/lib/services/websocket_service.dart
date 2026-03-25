import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/io.dart';

/// Real-time WebSocket service — receives danger scores,
/// zone alerts, SOS confirmations, and buddy alerts live.
class WebSocketService {
  static const _wsBase = 'ws://localhost:8000';

  WebSocketChannel? _channel;
  StreamController<Map<String, dynamic>>? _controller;
  Stream<Map<String, dynamic>>? _stream;
  Timer? _reconnectTimer;

  bool _connected = false;
  String? _userId;
  String? _token;

  /// Call once after login
  void connect(String userId, String token, {String city = 'MUM'}) {
    _userId = userId;
    _token  = token;
    _controller = StreamController<Map<String, dynamic>>.broadcast();
    _stream     = _controller!.stream;
    _doConnect(userId, token, city);
  }

  void _doConnect(String userId, String token, String city) {
    try {
      final uri = Uri.parse(
        '$_wsBase/ws/$userId?token=$token&city=$city',
      );
      _channel   = IOWebSocketChannel.connect(uri);
      _connected = true;

      _channel!.stream.listen(
        (raw) {
          final msg = jsonDecode(raw as String) as Map<String, dynamic>;
          _controller?.add(msg);
        },
        onDone: _onDisconnect,
        onError: (_) => _onDisconnect(),
      );
    } catch (e) {
      _onDisconnect();
    }
  }

  void _onDisconnect() {
    _connected = false;
    // Auto-reconnect after 5 seconds
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 5), () {
      if (_userId != null && _token != null) {
        _doConnect(_userId!, _token!, 'MUM');
      }
    });
  }

  /// Send a location ping to the server
  void sendLocation({
    required double lat,
    required double lng,
    double speed = 0.0,
    int dwellTime = 0,
    double crowdDensity = 0.3,
  }) {
    if (!_connected || _channel == null) return;
    final now = DateTime.now();
    _channel!.sink.add(jsonEncode({
      'lat':           lat,
      'lng':           lng,
      'speed':         speed,
      'dwell_time':    dwellTime,
      'hour':          now.hour,
      'crowd_density': crowdDensity,
    }));
  }

  /// Stream of all messages from the server
  Stream<Map<String, dynamic>>? get stream => _stream;

  /// Filtered streams by message type
  Stream<Map<String, dynamic>> get dangerScores =>
      stream!.where((m) => m['type'] == 'danger_score');

  Stream<Map<String, dynamic>> get zoneAlerts =>
      stream!.where((m) => m['type'] == 'zone_alert');

  Stream<Map<String, dynamic>> get sosConfirmations =>
      stream!.where((m) => m['type'] == 'sos_confirmed');

  Stream<Map<String, dynamic>> get buddyAlerts =>
      stream!.where((m) => m['type'] == 'buddy_alert');

  Stream<Map<String, dynamic>> get cityAlerts =>
      stream!.where((m) => m['type'] == 'city_alert');

  bool get isConnected => _connected;

  void dispose() {
    _reconnectTimer?.cancel();
    _channel?.sink.close();
    _controller?.close();
  }
}

/// Singleton instance
final wsService = WebSocketService();
