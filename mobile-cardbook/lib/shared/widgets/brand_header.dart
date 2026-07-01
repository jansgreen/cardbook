import 'package:flutter/material.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';

class BrandHeader extends StatelessWidget {
  const BrandHeader({
    this.trailing,
    super.key,
  });

  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(14),
          child: Image.asset(
            'assets/images/logo.png',
            width: 42,
            height: 42,
            fit: BoxFit.cover,
          ),
        ),
        const SizedBox(width: 10),
        const Text(
          'cardbook',
          style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900),
        ),
        const Spacer(),
        trailing ??
            IconButton(
              onPressed: () {},
              icon: const Icon(Icons.menu, color: AppColors.text),
            ),
      ],
    );
  }
}
