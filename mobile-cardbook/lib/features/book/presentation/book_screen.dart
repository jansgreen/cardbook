import 'package:flutter/material.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';

class BookScreen extends StatelessWidget {
  const BookScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: Center(child: Text('Book')),
        ),
      ),
      bottomNavigationBar: AppBottomNav(currentIndex: 4),
    );
  }
}
