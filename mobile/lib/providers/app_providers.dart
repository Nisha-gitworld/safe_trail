import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/risk_model.dart';
import '../services/api_service.dart';
import '../services/location_service.dart';

// ── Auth state ────────────────────────────────────────────────────────────────
class AuthState {
  final String? token;
  final String? userId;
  final bool    isLoggedIn;
  const AuthState({this.token, this.userId, this.isLoggedIn = false});
}

class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier() : super(const AuthState());

  Future<void> login(String email, String password) async {
    final token = await ApiService.login(email, password);
    state = AuthState(token: token, userId: email, isLoggedIn: true);
  }

  void logout() => state = const AuthState();
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>(
  (_) => AuthNotifier(),
);

// ── Live risk score ───────────────────────────────────────────────────────────
final riskProvider = FutureProvider.autoDispose<RiskResponse>((ref) async {
  final pos = await LocationService.getCurrentPosition();
  return ApiService.getRiskScore(
    lat: pos.latitude,
    lng: pos.longitude,
    hour: DateTime.now().hour,
  );
});

// ── Geofence zones ────────────────────────────────────────────────────────────
final zonesProvider = FutureProvider.family<List<dynamic>, String>((ref, city) async {
  return ApiService.getZones(city);
});

// ── Heatmap data ──────────────────────────────────────────────────────────────
final heatmapProvider = FutureProvider.family<List<Map<String, dynamic>>, String>(
  (ref, city) async => ApiService.getHeatmap(city),
);

// ── User profile ──────────────────────────────────────────────────────────────
final identityProvider = FutureProvider.autoDispose<Map<String, dynamic>>(
  (_) async => ApiService.getIdentityProfile(),
);

// ── WebSocket connection status ───────────────────────────────────────────────
final wsConnectedProvider = StateProvider<bool>((_) => false);

// ── Active incident ───────────────────────────────────────────────────────────
final activeIncidentProvider = StateProvider<Map<String, dynamic>?>((_) => null);

// ── Group state ───────────────────────────────────────────────────────────────
final groupIdProvider    = StateProvider<String?>((_) => null);
final groupStatusProvider = FutureProvider.family<Map<String, dynamic>, String>(
  (ref, groupId) async {
    // Would call: GET /api/buddy/groups/{groupId}/status
    await Future.delayed(const Duration(milliseconds: 500));
    return {"group_id": groupId, "member_count": 0, "online_count": 0};
  },
);
