import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/features/push/data/push_repository.dart';

final pushNotificationControllerProvider =
    Provider<PushNotificationController>((ref) {
  return PushNotificationController(ref);
});

@pragma('vm:entry-point')
Future<void> cardbookFirebaseMessagingBackgroundHandler(
  RemoteMessage message,
) async {
  try {
    if (Firebase.apps.isEmpty) {
      await Firebase.initializeApp();
    }
  } catch (_) {
    // Firebase can be absent in local/internal builds.
  }
}

class PushNotificationController {
  PushNotificationController(this._ref);

  final Ref _ref;

  static bool _initialized = false;
  static bool _available = false;

  static bool get isAvailable => _available;

  static Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;

    try {
      if (Firebase.apps.isEmpty) {
        await Firebase.initializeApp();
      }
      FirebaseMessaging.onBackgroundMessage(
        cardbookFirebaseMessagingBackgroundHandler,
      );
      _available = true;
    } catch (error) {
      _available = false;
      if (kDebugMode) {
        debugPrint('Cardbook push disabled: $error');
      }
    }
  }

  Future<PushRegistrationResult> registerDevice() async {
    await initialize();
    if (!_available) {
      return const PushRegistrationResult(
        registered: false,
        message: 'Firebase no esta configurado para este build.',
      );
    }

    try {
      final messaging = FirebaseMessaging.instance;
      final settings = await messaging.requestPermission(
        alert: true,
        badge: true,
        sound: true,
      );
      if (settings.authorizationStatus == AuthorizationStatus.denied) {
        return const PushRegistrationResult(
          registered: false,
          message: 'Permiso de notificaciones denegado.',
        );
      }

      final token = await messaging.getToken();
      if (token == null || token.isEmpty) {
        return const PushRegistrationResult(
          registered: false,
          message: 'Firebase no devolvio token FCM.',
        );
      }

      await _ref.read(pushRepositoryProvider).registerDevice(token: token);
      FirebaseMessaging.instance.onTokenRefresh.listen((newToken) {
        _ref.read(pushRepositoryProvider).registerDevice(token: newToken);
      });

      return const PushRegistrationResult(
        registered: true,
        message: 'Notificaciones push activadas.',
      );
    } catch (error) {
      return PushRegistrationResult(
        registered: false,
        message: 'No pudimos activar push: $error',
      );
    }
  }

  Future<PushRegistrationResult> sendTest() async {
    try {
      await _ref.read(pushRepositoryProvider).sendTest();
      return const PushRegistrationResult(
        registered: true,
        message: 'Prueba push procesada.',
      );
    } catch (error) {
      return PushRegistrationResult(
        registered: false,
        message: 'No pudimos enviar prueba push: $error',
      );
    }
  }
}

class PushRegistrationResult {
  const PushRegistrationResult({
    required this.registered,
    required this.message,
  });

  final bool registered;
  final String message;
}
