import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/platform/native_actions.dart';
import 'package:mobile_cardbook/features/marketplace/data/marketplace_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/offline_notice.dart';
import 'package:mobile_cardbook/shared/widgets/section_header.dart';
import 'package:mobile_cardbook/shared/widgets/share_center.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class MarketplaceScreen extends ConsumerStatefulWidget {
  const MarketplaceScreen({super.key});

  @override
  ConsumerState<MarketplaceScreen> createState() => _MarketplaceScreenState();
}

class _MarketplaceScreenState extends ConsumerState<MarketplaceScreen> {
  late final TextEditingController _search;

  @override
  void initState() {
    super.initState();
    _search = TextEditingController(text: ref.read(marketplaceQueryProvider));
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  void _submitSearch() {
    ref.read(marketplaceQueryProvider.notifier).state = _search.text.trim();
  }

  @override
  Widget build(BuildContext context) {
    final marketplace = ref.watch(marketplaceProvider);

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(marketplaceProvider);
              await ref.read(marketplaceProvider.future);
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
              children: [
                const BrandHeader(),
                const SizedBox(height: 24),
                const _MarketplaceHero(),
                const SizedBox(height: 18),
                _SearchBox(
                  controller: _search,
                  onSubmitted: _submitSearch,
                ),
                const SizedBox(height: 18),
                marketplace.when(
                  loading: () => const SizedBox(
                    height: 220,
                    child: AsyncStateView.loading(),
                  ),
                  error: (_, __) => const AsyncStateView.error(
                    'No pudimos cargar el explorador.',
                  ),
                  data: (data) => _MarketplaceContent(data: data),
                ),
              ],
            ),
          ),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: null),
    );
  }
}

class _MarketplaceHero extends StatelessWidget {
  const _MarketplaceHero();

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      gradient: AppGradients.cardGlow,
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          StatusBadge(
            label: 'Explorar',
            icon: Icons.travel_explore_rounded,
            color: AppColors.gold,
          ),
          SizedBox(height: 16),
          Text(
            'Empresas, talento y websites',
            style: TextStyle(
                fontSize: 28, height: 1.05, fontWeight: FontWeight.w900),
          ),
          SizedBox(height: 8),
          Text(
            'Busca tarjetas de negocio, White Card Jobs y websites publicados en Cardbook.',
            style: TextStyle(color: AppColors.muted, height: 1.45),
          ),
        ],
      ),
    );
  }
}

class _SearchBox extends StatelessWidget {
  const _SearchBox({
    required this.controller,
    required this.onSubmitted,
  });

  final TextEditingController controller;
  final VoidCallback onSubmitted;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(12),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              textInputAction: TextInputAction.search,
              onSubmitted: (_) => onSubmitted(),
              decoration: const InputDecoration(
                prefixIcon: Icon(Icons.search_rounded),
                labelText: 'Buscar empresas, servicios o talento',
              ),
            ),
          ),
          const SizedBox(width: 10),
          SizedBox(
            height: 54,
            child: FilledButton(
              onPressed: onSubmitted,
              child: const Icon(Icons.tune_rounded),
            ),
          ),
        ],
      ),
    );
  }
}

class _MarketplaceContent extends StatelessWidget {
  const _MarketplaceContent({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final summary = data['summary'] is Map<String, dynamic>
        ? data['summary'] as Map<String, dynamic>
        : const <String, dynamic>{};
    final cards = _items(data['business_cards']);
    final jobs = _items(data['white_card_jobs']);
    final websites = _items(data['websites']);
    final isOffline = data['_offline'] == true;

    return Column(
      children: [
        if (isOffline) ...[
          const OfflineNotice(),
          const SizedBox(height: 18),
        ],
        _SummaryGrid(summary: summary),
        const SizedBox(height: 18),
        _ResultSection(
          title: 'Tarjetas de negocio',
          empty: 'No encontramos tarjetas con esa busqueda.',
          items: cards,
        ),
        const SizedBox(height: 18),
        _ResultSection(
          title: 'White Card Jobs',
          empty: 'No encontramos perfiles laborales.',
          items: jobs,
        ),
        const SizedBox(height: 18),
        _ResultSection(
          title: 'Websites publicados',
          empty: 'No encontramos websites publicados.',
          items: websites,
        ),
      ],
    );
  }
}

class _SummaryGrid extends StatelessWidget {
  const _SummaryGrid({required this.summary});

  final Map<String, dynamic> summary;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Row(
        children: [
          Expanded(
            child: _SummaryPill(
              label: 'Tarjetas',
              value: _text(summary['business_cards'], fallback: '0'),
              color: AppColors.blue,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _SummaryPill(
              label: 'Jobs',
              value: _text(summary['white_card_jobs'], fallback: '0'),
              color: AppColors.gold,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _SummaryPill(
              label: 'Websites',
              value: _text(summary['websites'], fallback: '0'),
              color: AppColors.green,
            ),
          ),
        ],
      ),
    );
  }
}

class _SummaryPill extends StatelessWidget {
  const _SummaryPill({
    required this.label,
    required this.value,
    required this.color,
  });

  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: .12),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: color.withValues(alpha: .28)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(value,
              style:
                  const TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
          const SizedBox(height: 2),
          Text(label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: AppColors.muted, fontSize: 12)),
        ],
      ),
    );
  }
}

class _ResultSection extends StatelessWidget {
  const _ResultSection({
    required this.title,
    required this.empty,
    required this.items,
  });

  final String title;
  final String empty;
  final List<Map<String, dynamic>> items;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(title: title, actionLabel: '${items.length}'),
          const SizedBox(height: 12),
          if (items.isEmpty)
            AsyncStateView.empty(empty)
          else
            for (final item in items) ...[
              _MarketplaceTile(item: item),
              const SizedBox(height: 10),
            ],
        ],
      ),
    );
  }
}

class _MarketplaceTile extends StatelessWidget {
  const _MarketplaceTile({required this.item});

  final Map<String, dynamic> item;

  @override
  Widget build(BuildContext context) {
    final title = _text(item['title'], fallback: 'Cardbook');
    final subtitle = _text(item['subtitle']);
    final company = _text(item['company']);
    final category = _text(item['category']);
    final publicUrl = _text(item['public_url']);
    final photo = _text(item['photo']);
    final logo = _text(item['logo']);
    final image = photo.isNotEmpty ? photo : logo;
    final type = _typeLabel(_text(item['type']));

    return InkWell(
      onTap: publicUrl.isEmpty ? null : () => NativeActions.website(publicUrl),
      borderRadius: BorderRadius.circular(AppRadius.md),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.inkAlt.withValues(alpha: .72),
          borderRadius: BorderRadius.circular(AppRadius.md),
          border: Border.all(color: AppColors.stroke),
        ),
        child: Row(
          children: [
            _Avatar(imageUrl: image, title: title),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  StatusBadge(
                    label: type,
                    icon: Icons.verified_rounded,
                    color: AppColors.purple,
                  ),
                  const SizedBox(height: 8),
                  Text(title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w900)),
                  if (subtitle.isNotEmpty) ...[
                    const SizedBox(height: 3),
                    Text(subtitle,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: AppColors.muted)),
                  ],
                  if (company.isNotEmpty || category.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(
                      [company, category]
                          .where((value) => value.isNotEmpty)
                          .join(' - '),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style:
                          const TextStyle(color: AppColors.cyan, fontSize: 12),
                    ),
                  ],
                ],
              ),
            ),
            IconButton(
              onPressed: publicUrl.isEmpty
                  ? null
                  : () => ShareCenter.show(
                        context,
                        SharePayload(
                          type: _shareType(_text(item['type'])),
                          title: title,
                          subtitle: subtitle.isEmpty
                              ? 'Disponible en Cardbook'
                              : subtitle,
                          url: publicUrl,
                          organization: company,
                          website: publicUrl,
                        ),
                      ),
              icon: const Icon(Icons.ios_share_rounded),
            ),
          ],
        ),
      ),
    );
  }
}

class _Avatar extends StatelessWidget {
  const _Avatar({required this.imageUrl, required this.title});

  final String imageUrl;
  final String title;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 58,
      height: 58,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: AppColors.panelSoft,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.stroke),
      ),
      child: imageUrl.isEmpty
          ? Center(
              child: Text(
                _initials(title),
                style: const TextStyle(fontWeight: FontWeight.w900),
              ),
            )
          : Image.network(
              imageUrl,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => Center(
                child: Text(
                  _initials(title),
                  style: const TextStyle(fontWeight: FontWeight.w900),
                ),
              ),
            ),
    );
  }
}

List<Map<String, dynamic>> _items(dynamic value) {
  if (value is List) return value.whereType<Map<String, dynamic>>().toList();
  return [];
}

String _text(dynamic value, {String fallback = ''}) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
}

String _typeLabel(String type) {
  return switch (type) {
    'white_card_job' => 'White Card',
    'website' => 'Website',
    'business_card' => 'Tarjeta',
    _ => 'Cardbook',
  };
}

ShareTargetType _shareType(String type) {
  return switch (type) {
    'white_card_job' => ShareTargetType.whiteCardJob,
    'website' => ShareTargetType.website,
    'business_card' => ShareTargetType.businessCard,
    _ => ShareTargetType.company,
  };
}

String _initials(String value) {
  final words = value
      .trim()
      .split(RegExp(r'\s+'))
      .where((word) => word.isNotEmpty)
      .toList();
  if (words.isEmpty) return 'CB';
  if (words.length == 1) {
    return words.first
        .substring(0, words.first.length >= 2 ? 2 : 1)
        .toUpperCase();
  }
  return '${words[0][0]}${words[1][0]}'.toUpperCase();
}
