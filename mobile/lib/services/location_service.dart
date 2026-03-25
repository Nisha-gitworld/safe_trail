// ── location_service.dart ─────────────────────────────────────────────────
import 'package:geolocator/geolocator.dart';

class LocationService {
  static Future<Position> getCurrentPosition() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) throw Exception('Location services are disabled.');

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        throw Exception('Location permissions denied.');
      }
    }
    if (permission == LocationPermission.deniedForever) {
      throw Exception('Location permissions permanently denied.');
    }

    return Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.high,
    );
  }

  static Stream<Position> getPositionStream({int intervalMs = 10000}) {
    return Geolocator.getPositionStream(
      locationSettings: LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10,         // metres before next update
      ),
    );
  }

  /// Adaptive ping interval based on speed
  static int adaptivePingIntervalMs(double speedMs) {
    if (speedMs > 5.0) return 5000;   // fast moving — every 5s
    if (speedMs > 1.0) return 15000;  // walking — every 15s
    return 30000;                     // stationary — every 30s
  }
}
