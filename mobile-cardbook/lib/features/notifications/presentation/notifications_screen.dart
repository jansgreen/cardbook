import 'package:flutter/material.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';

class NotificationsScreen extends StatelessWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: Center(child: Text('Notificaciones')),
        ),
      ),
      bottomNavigationBar: AppBottomNav(currentIndex: 3),
    );
  }
}
