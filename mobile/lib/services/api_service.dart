import 'package:dio/dio.dart';
import '../models/risk_model.dart';

class ApiService {
  static const _baseUrl = 'http://localhost:8000/api';  // change to your backend URL

  static final _dio = Dio(BaseOptions(
    baseUrl: _baseUrl,
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 15),
    headers: {'Content-Type': 'application/json'},
  ));

  // Store JWT in memory (use flutter_secure_storage in production)
  static String? _token;

  static void setToken(String token) {
    _token = token;
    _dio.options.headers['Authorization'] = 'Bearer $token';
  }

  // ── Auth ──────────────────────────────────────────────────────────────────
  static Future<String> login(String email, String password) async {
    final res = await _dio.post('/auth/login', data: {'email': email, 'password': password});
    final token = res.data['access_token'] as String;
    setToken(token);
    return token;
  }

  static Future<void> register(Map<String, dynamic> userData) async {
    await _dio.post('/auth/register', data: userData);
  }

  // ── Risk ──────────────────────────────────────────────────────────────────
  static Future<RiskResponse> getRiskScore({
    required double lat,
    required double lng,
    required int hour,
    double speed = 0.0,
    int dwellTime = 0,
    double crowdDensity = 0.3,
  }) async {
    try {
      final res = await _dio.post('/risk/score', data: {
        'lat': lat, 'lng': lng, 'speed': speed,
        'dwell_time': dwellTime, 'hour': hour,
        'crowd_density': crowdDensity, 'user_id': 'me',
      });
      return RiskResponse.fromJson(res.data);
    } catch (e) {
      // Offline fallback — return safe score
      return RiskResponse(dangerScore: 20, zoneType: 'safe', alertLevel: 0,
          recommendation: 'Offline mode — stay alert');
    }
  }

  static Future<List<Map<String, dynamic>>> getHeatmap(String city) async {
    final res = await _dio.get('/risk/heatmap', queryParameters: {'city': city});
    return List<Map<String, dynamic>>.from(res.data['cells']);
  }

  // ── Geofence ──────────────────────────────────────────────────────────────
  static Future<Map<String, dynamic>> checkGeofence(double lat, double lng) async {
    final res = await _dio.post('/geofence/check', data: {'lat': lat, 'lng': lng, 'user_id': 'me'});
    return res.data;
  }

  static Future<List<dynamic>> getZones(String city) async {
    final res = await _dio.get('/geofence/zones', queryParameters: {'city': city});
    return res.data['zones'];
  }

  // ── SOS ───────────────────────────────────────────────────────────────────
  static Future<Map<String, dynamic>> triggerSOS({
    required double lat,
    required double lng,
    String? incidentType,
    String? description,
  }) async {
    final res = await _dio.post('/incident/sos', data: {
      'user_id': 'me', 'lat': lat, 'lng': lng,
      'incident_type': incidentType ?? 'ACCIDENT',
      'description': description,
    });
    return res.data;
  }

  // ── Identity ──────────────────────────────────────────────────────────────
  static Future<Map<String, dynamic>> getIdentityProfile() async {
    final res = await _dio.get('/identity/profile');
    return res.data;
  }
}
