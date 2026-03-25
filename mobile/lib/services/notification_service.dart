// ── notification_service.dart ─────────────────────────────────────────────
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotificationService {
  static final _localNotifications = FlutterLocalNotificationsPlugin();

  static Future<void> init() async {
    // Local notifications setup
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    await _localNotifications.initialize(
      const InitializationSettings(android: androidSettings, iOS: iosSettings),
    );

    // FCM
    await FirebaseMessaging.instance.requestPermission();
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
    FirebaseMessaging.onBackgroundMessage(_firebaseBackgroundHandler);
  }

  static Future<void> _handleForegroundMessage(RemoteMessage msg) async {
    const channel = AndroidNotificationChannel(
      'safetrail_alerts', 'SafeTrail Alerts',
      importance: Importance.max,
    );
    await _localNotifications.show(
      msg.hashCode,
      msg.notification?.title ?? 'SafeTrail Alert',
      msg.notification?.body,
      NotificationDetails(android: AndroidNotificationDetails(
        channel.id, channel.name, importance: Importance.max,
        icon: '@mipmap/ic_launcher',
      )),
    );
  }

  static Future<void> showDangerAlert(String message) async {
    await _localNotifications.show(
      999,
      '⚠️ Safety Alert',
      message,
      const NotificationDetails(android: AndroidNotificationDetails(
        'danger_alerts', 'Danger Alerts',
        importance: Importance.max, priority: Priority.high,
        color: Color(0xFFE24B4A),
      )),
    );
  }
}

@pragma('vm:entry-point')
Future<void> _firebaseBackgroundHandler(RemoteMessage message) async {
  // Handle background FCM
}
