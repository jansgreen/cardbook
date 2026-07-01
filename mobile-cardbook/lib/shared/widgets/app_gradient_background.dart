import 'package:flutter/material.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';

class AppGradientBackground extends StatelessWidget {
  const AppGradientBackground({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF111B5E), AppColors.ink, Color(0xFF061322)],
          stops: [0, .42, 1],
        ),
      ),
      child: child,
    );
  }
}
