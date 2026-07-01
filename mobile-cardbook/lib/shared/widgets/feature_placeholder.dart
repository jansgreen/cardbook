import 'package:flutter/material.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class FeaturePlaceholder extends StatelessWidget {
  const FeaturePlaceholder({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.badge,
    super.key,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final String badge;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
      children: [
        const BrandHeader(),
        const SizedBox(height: 28),
        GlassCard(
          padding: const EdgeInsets.all(22),
          gradient: AppGradients.cardGlow,
          borderColor: AppColors.blue.withOpacity(.24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              StatusBadge(label: badge, icon: Icons.auto_awesome_rounded, color: AppColors.gold),
              const SizedBox(height: 22),
              Container(
                width: 64,
                height: 64,
                decoration: BoxDecoration(
                  gradient: AppGradients.primary,
                  borderRadius: BorderRadius.circular(AppRadius.lg),
                ),
                child: Icon(icon, size: 30),
              ),
              const SizedBox(height: 22),
              Text(
                title,
                style: const TextStyle(fontSize: 32, height: 1.05, fontWeight: FontWeight.w900),
              ),
              const SizedBox(height: 12),
              Text(
                subtitle,
                style: const TextStyle(color: AppColors.muted, fontSize: 16, height: 1.5),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
