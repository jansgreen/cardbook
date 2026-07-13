import 'package:flutter/material.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';

class AsyncStateView extends StatelessWidget {
  const AsyncStateView.loading({this.message, super.key})
      : isError = false,
        title = null,
        icon = null,
        actionLabel = null,
        onAction = null;

  const AsyncStateView.empty(
    this.message, {
    this.title,
    this.icon,
    this.actionLabel,
    this.onAction,
    super.key,
  }) : isError = false;

  const AsyncStateView.error(
    this.message, {
    this.title,
    this.icon,
    this.actionLabel,
    this.onAction,
    super.key,
  }) : isError = true;

  final String? message;
  final String? title;
  final IconData? icon;
  final String? actionLabel;
  final VoidCallback? onAction;
  final bool isError;

  @override
  Widget build(BuildContext context) {
    if (message == null && title == null) {
      return Semantics(
        label: 'Cargando contenido',
        child: const Center(
          child: CircularProgressIndicator(
              strokeWidth: 3, color: AppColors.purple),
        ),
      );
    }

    final stateIcon = icon ??
        (isError ? Icons.warning_amber_rounded : Icons.info_outline_rounded);
    final color = isError ? AppColors.red : AppColors.purple;

    return GlassCard(
      borderColor: color.withValues(alpha: .32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: .14),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(stateIcon, color: color),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title ?? (isError ? 'Algo no cargo bien' : 'Sin datos'),
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    if (message != null && message!.isNotEmpty) ...[
                      const SizedBox(height: 5),
                      Text(
                        message!,
                        style: const TextStyle(
                          color: AppColors.muted,
                          height: 1.35,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
          if (actionLabel != null && onAction != null) ...[
            const SizedBox(height: 14),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: onAction,
                icon: Icon(isError ? Icons.refresh_rounded : Icons.add_rounded),
                label: Text(actionLabel!),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
