import 'package:flutter/material.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';

class CompaniesScreen extends StatelessWidget {
  const CompaniesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: Center(child: Text('Empresas')),
        ),
      ),
      bottomNavigationBar: AppBottomNav(currentIndex: 1),
    );
  }
}
