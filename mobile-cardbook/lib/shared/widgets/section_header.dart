import 'package:flutter/material.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';

class SectionHeader extends StatelessWidget {
  const SectionHeader({
    required this.title,
    this.actionLabel,
    this.onAction,
    super.key,
  });

  final String title;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Text(
            title,
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900),
          ),
        ),
        if (actionLabel != null)
          TextButton(
            onPressed: onAction ?? () {},
            child: Text(actionLabel!,
                style: const TextStyle(color: AppColors.purple)),
          ),
      ],
    );
  }
}
