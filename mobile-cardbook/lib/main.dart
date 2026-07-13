import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/app/cardbook_app.dart';
import 'package:mobile_cardbook/features/push/data/push_notification_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await PushNotificationController.initialize();
  runApp(const ProviderScope(child: CardbookApp()));
}
