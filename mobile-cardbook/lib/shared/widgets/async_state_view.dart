import 'package:flutter/material.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';

class AsyncStateView extends StatelessWidget {
  const AsyncStateView.loading({super.key})
      : message = null,
        isError = false;

  const AsyncStateView.empty(this.message, {super.key}) : isError = false;

  const AsyncStateView.error(this.message, {super.key}) : isError = true;

  final String? message;
  final bool isError;

  @override
  Widget build(BuildContext context) {
    if (message == null) {
      return const Center(
        child: CircularProgressIndicator(strokeWidth: 3, color: AppColors.purple),
      );
    }

    return GlassCard(
      child: Row(
        children: [
          Icon(
            isError ? Icons.warning_amber_rounded : Icons.info_outline_rounded,
            color: isError ? AppColors.red : AppColors.muted,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              message!,
              style: const TextStyle(color: AppColors.muted, height: 1.35),
            ),
          ),
        ],
      ),
    );
  }
}
