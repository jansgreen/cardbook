import 'package:flutter/material.dart';
import 'package:mobile_cardbook/app/router.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';

class CardbookApp extends StatelessWidget {
  const CardbookApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Cardbook',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark(),
      routerConfig: appRouter,
    );
  }
}
