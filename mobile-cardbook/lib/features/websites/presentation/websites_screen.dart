import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/platform/native_actions.dart';
import 'package:mobile_cardbook/features/websites/data/websites_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/section_header.dart';
import 'package:mobile_cardbook/shared/widgets/share_center.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class WebsitesScreen extends ConsumerWidget {
  const WebsitesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final websites = ref.watch(mobileWebsitesProvider);
    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
            children: [
              const BrandHeader(),
              const SizedBox(height: 24),
              const _WebsitesHero(),
              const SizedBox(height: 18),
              GlassCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SectionHeader(
                        title: 'Websites', actionLabel: 'Builder'),
                    const SizedBox(height: 12),
                    websites.when(
                      loading: () => const SizedBox(
                          height: 160, child: AsyncStateView.loading()),
                      error: (_, __) => const AsyncStateView.error(
                          'No pudimos cargar tus websites.'),
                      data: (items) => items.isEmpty
                          ? const AsyncStateView.empty(
                              'Cuando actives Website Builder, tus sitios apareceran aqui.')
                          : Column(
                              children: [
                                for (final website in items) ...[
                                  _WebsiteTile(website: website),
                                  const SizedBox(height: 10),
                                ],
                              ],
                            ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: null),
    );
  }
}

class _WebsiteTile extends StatelessWidget {
  const _WebsiteTile({required this.website});

  final Map<String, dynamic> website;

  @override
  Widget build(BuildContext context) {
    final title = _text(website['title'], fallback: 'Website Cardbook');
    final url = _text(website['public_url']);
    final published = website['is_published'] == true;
    final status = website['publish_status'] is Map<String, dynamic>
        ? website['publish_status'] as Map<String, dynamic>
        : {};
    final issues = (status['issues'] as List<dynamic>? ?? [])
        .map((item) => item.toString())
        .toList();
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.inkAlt.withValues(alpha: .72),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.stroke),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: LinearGradient(colors: [
                    Color(_color(website['primary_color'])),
                    Color(_color(website['accent_color']))
                  ]),
                ),
                child: const Icon(Icons.public_rounded, color: Colors.white),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontWeight: FontWeight.w900)),
                    const SizedBox(height: 4),
                    Text(published ? 'Publicado' : 'Borrador',
                        style: TextStyle(
                            color: published ? AppColors.green : AppColors.gold,
                            fontWeight: FontWeight.w800)),
                  ],
                ),
              ),
              IconButton(
                onPressed: url.isEmpty
                    ? null
                    : () => ShareCenter.show(
                          context,
                          SharePayload(
                            type: ShareTargetType.website,
                            title: title,
                            subtitle: published
                                ? 'Website publicado'
                                : 'Website en borrador',
                            url: url,
                            website: url,
                          ),
                        ),
                icon:
                    const Icon(Icons.ios_share_rounded, color: AppColors.text),
              ),
              IconButton(
                onPressed:
                    url.isEmpty ? null : () => NativeActions.website(url),
                icon: const Icon(Icons.open_in_new_rounded,
                    color: AppColors.text),
              ),
            ],
          ),
          if (issues.isNotEmpty) ...[
            const SizedBox(height: 12),
            for (final issue in issues.take(3))
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text('- $issue',
                    style:
                        const TextStyle(color: AppColors.muted, fontSize: 12)),
              ),
          ],
          if (url.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(url,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: AppColors.purple, fontSize: 12)),
          ],
        ],
      ),
    );
  }
}

class _WebsitesHero extends StatelessWidget {
  const _WebsitesHero();

  @override
  Widget build(BuildContext context) {
    return const GlassCard(
      gradient: AppGradients.cardGlow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          StatusBadge(
              label: 'Website Builder',
              icon: Icons.language_rounded,
              color: AppColors.gold),
          SizedBox(height: 16),
          Text('Sitios web',
              style: TextStyle(
                  fontSize: 32, height: 1.05, fontWeight: FontWeight.w900)),
          SizedBox(height: 8),
          Text(
              'Administra la presencia publica de tus empresas desde la app movil.',
              style: TextStyle(color: AppColors.muted, height: 1.45)),
        ],
      ),
    );
  }
}

String _text(dynamic value, {String fallback = ''}) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
}

int _color(dynamic value) {
  final raw = _text(value, fallback: '#3B36FF').replaceFirst('#', '');
  return int.tryParse('0xFF$raw') ?? 0xFF3B36FF;
}
