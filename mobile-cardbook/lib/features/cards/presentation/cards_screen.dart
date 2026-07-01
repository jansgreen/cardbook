import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/cards/data/cards_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/section_header.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class CardsScreen extends ConsumerWidget {
  const CardsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final digitalCards = ref.watch(digitalCardsProvider);
    final businessCards = ref.watch(businessCardsProvider);

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
            children: [
              const BrandHeader(),
              const SizedBox(height: 24),
              const _CardsHero(),
              const SizedBox(height: 18),
              _CardsSection(
                title: 'Perfiles de negocio',
                actionLabel: 'Crear perfil',
                onAction: () => context.push('/cards/digital/form'),
                state: digitalCards,
                emptyMessage: 'Aun no tienes perfiles de negocio.',
                itemBuilder: (card) => _DigitalCardTile(card: card),
              ),
              const SizedBox(height: 18),
              _CardsSection(
                title: 'Tarjetas de presentacion',
                actionLabel: 'Crear tarjeta',
                onAction: () => context.push('/cards/business/form'),
                state: businessCards,
                emptyMessage: 'Aun no tienes tarjetas de presentacion.',
                itemBuilder: (card) => _BusinessCardTile(card: card),
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: 2),
    );
  }
}

class _CardsSection extends StatelessWidget {
  const _CardsSection({
    required this.title,
    required this.actionLabel,
    required this.onAction,
    required this.state,
    required this.emptyMessage,
    required this.itemBuilder,
  });

  final String title;
  final String actionLabel;
  final VoidCallback onAction;
  final AsyncValue<List<Map<String, dynamic>>> state;
  final String emptyMessage;
  final Widget Function(Map<String, dynamic>) itemBuilder;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(title: title, actionLabel: actionLabel, onAction: onAction),
          const SizedBox(height: 12),
          state.when(
            loading: () => const SizedBox(height: 120, child: AsyncStateView.loading()),
            error: (_, __) => AsyncStateView.error('No pudimos cargar $title.'),
            data: (items) => items.isEmpty
                ? AsyncStateView.empty(emptyMessage)
                : Column(
                    children: [
                      for (final item in items) ...[
                        itemBuilder(item),
                        const SizedBox(height: 10),
                      ],
                    ],
                  ),
          ),
        ],
      ),
    );
  }
}

class _DigitalCardTile extends StatelessWidget {
  const _DigitalCardTile({required this.card});

  final Map<String, dynamic> card;

  @override
  Widget build(BuildContext context) {
    final jobTitle = _cleanText(card['job_title']);
    return _CardTile(
      title: jobTitle.isNotEmpty ? jobTitle : 'Perfil de negocio',
      subtitle: _firstText([card['email'], card['phone_number']], fallback: 'Tarjeta digital'),
      icon: Icons.badge_rounded,
      accent: AppColors.blue,
      slug: card['slug']?.toString(),
      onTap: () => context.push('/cards/detail', extra: {'kind': 'digital', 'card': card}),
    );
  }
}

class _BusinessCardTile extends StatelessWidget {
  const _BusinessCardTile({required this.card});

  final Map<String, dynamic> card;

  @override
  Widget build(BuildContext context) {
    return _CardTile(
      title: _firstText([card['display_name']], fallback: 'Tarjeta de presentacion'),
      subtitle: _firstText([card['company_name'], card['job_title']], fallback: 'Presentacion empresarial'),
      icon: Icons.contact_page_rounded,
      accent: AppColors.gold,
      slug: card['slug']?.toString(),
      onTap: () => context.push('/cards/detail', extra: {'kind': 'business', 'card': card}),
    );
  }
}

String _cleanText(dynamic value) {
  return value?.toString().trim() ?? '';
}

String _firstText(List<dynamic> values, {required String fallback}) {
  for (final value in values) {
    final text = _cleanText(value);
    if (text.isNotEmpty) return text;
  }
  return fallback;
}

class _CardTile extends StatelessWidget {
  const _CardTile({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.accent,
    this.slug,
    this.onTap,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final Color accent;
  final String? slug;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppRadius.md),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.inkAlt.withOpacity(.72),
          borderRadius: BorderRadius.circular(AppRadius.md),
          border: Border.all(color: AppColors.stroke),
        ),
        child: Row(
          children: [
            Container(
              width: 50,
              height: 50,
              decoration: BoxDecoration(
                color: accent.withOpacity(.14),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(icon, color: accent),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w900)),
                  const SizedBox(height: 4),
                  Text(subtitle, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: AppColors.muted, fontSize: 12)),
                  if (slug != null && slug!.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(slug!, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: AppColors.purple, fontSize: 12)),
                  ],
                ],
              ),
            ),
            const Icon(Icons.chevron_right_rounded, color: AppColors.muted),
          ],
        ),
      ),
    );
  }
}

class _CardsHero extends StatelessWidget {
  const _CardsHero();

  @override
  Widget build(BuildContext context) {
    return const GlassCard(
      gradient: AppGradients.cardGlow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          StatusBadge(label: 'Tarjetas digitales', icon: Icons.qr_code_2_rounded, color: AppColors.gold),
          SizedBox(height: 16),
          Text('Tarjetas', style: TextStyle(fontSize: 32, height: 1.05, fontWeight: FontWeight.w900)),
          SizedBox(height: 8),
          Text(
            'Gestiona perfiles de negocio, presentaciones y enlaces publicos.',
            style: TextStyle(color: AppColors.muted, height: 1.45),
          ),
        ],
      ),
    );
  }
}
