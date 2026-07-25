import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/cards/data/business_card_draft_store.dart';
import 'package:mobile_cardbook/features/cards/data/cards_repository.dart';
import 'package:mobile_cardbook/features/home/data/mobile_bootstrap_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/section_header.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class CardsScreen extends ConsumerStatefulWidget {
  const CardsScreen({super.key});

  @override
  ConsumerState<CardsScreen> createState() => _CardsScreenState();
}

class _CardsScreenState extends ConsumerState<CardsScreen> {
  final _search = TextEditingController();

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final digitalCards = ref.watch(digitalCardsProvider);
    final businessCards = ref.watch(businessCardsProvider);
    final businessDraft = ref.watch(businessCardDraftProvider);
    final bootstrap = ref.watch(mobileBootstrapProvider).valueOrNull;
    final canCreateDigital = bootstrap?.can('can_create_digital_card') ?? false;
    final canCreateBusiness =
        bootstrap?.can('can_create_business_card') ?? false;

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(digitalCardsProvider);
              ref.invalidate(businessCardsProvider);
              await Future.wait([
                ref.read(digitalCardsProvider.future),
                ref.read(businessCardsProvider.future),
              ]);
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
              children: [
                const BrandHeader(),
                const SizedBox(height: 24),
                const _CardsHero(),
                const SizedBox(height: 18),
                TextField(
                  controller: _search,
                  onChanged: (_) => setState(() {}),
                  decoration: InputDecoration(
                    hintText: 'Buscar tarjeta, empresa, cargo o contacto',
                    prefixIcon: const Icon(Icons.search_rounded),
                    suffixIcon: _search.text.trim().isEmpty
                        ? const Icon(Icons.filter_list_rounded)
                        : IconButton(
                            onPressed: () {
                              _search.clear();
                              setState(() {});
                            },
                            icon: const Icon(Icons.close_rounded),
                          ),
                  ),
                ),
                const SizedBox(height: 18),
                _CardsSection(
                  title: 'Perfiles de negocio',
                  actionLabel: canCreateDigital ? 'Crear perfil' : null,
                  onAction: canCreateDigital
                      ? () => context.push('/cards/digital/form')
                      : null,
                  onRetry: () => ref.invalidate(digitalCardsProvider),
                  state: digitalCards,
                  emptyMessage: 'Aun no tienes perfiles de negocio.',
                  filter: _filterCards,
                  itemBuilder: (card) => _DigitalCardTile(card: card),
                ),
                const SizedBox(height: 18),
                _CardsSection(
                  title: 'Tarjetas de presentacion',
                  actionLabel: canCreateBusiness ? 'Crear tarjeta' : null,
                  onAction: canCreateBusiness
                      ? () => context.push('/cards/business/form')
                      : null,
                  onRetry: () => ref.invalidate(businessCardsProvider),
                  state: businessCards,
                  emptyMessage: 'Aun no tienes tarjetas de presentacion.',
                  filter: _filterCards,
                  header: canCreateBusiness
                      ? businessDraft.when(
                          data: (draft) => draft == null
                              ? const SizedBox.shrink()
                              : _PendingDraftCard(
                                  draft: draft,
                                  onContinue: () =>
                                      context.push('/cards/business/form'),
                                  onDiscard: () async {
                                    await ref
                                        .read(businessCardDraftStoreProvider)
                                        .clear();
                                    ref.invalidate(businessCardDraftProvider);
                                  },
                                ),
                          loading: () => const SizedBox.shrink(),
                          error: (_, __) => const SizedBox.shrink(),
                        )
                      : null,
                  itemBuilder: (card) => _BusinessCardTile(card: card),
                ),
              ],
            ),
          ),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: 2),
    );
  }

  List<Map<String, dynamic>> _filterCards(List<Map<String, dynamic>> items) {
    final query = _search.text.trim().toLowerCase();
    if (query.isEmpty) return items;
    return items.where((card) {
      final haystack = [
        card['display_name'],
        card['company_name'],
        card['job_title'],
        card['email'],
        card['phone_number'],
        card['website'],
        card['slug'],
      ].map((value) => value?.toString().toLowerCase() ?? '').join(' ');
      return haystack.contains(query);
    }).toList();
  }
}

class _CardsSection extends StatelessWidget {
  const _CardsSection({
    required this.title,
    required this.actionLabel,
    required this.onAction,
    required this.onRetry,
    required this.state,
    required this.emptyMessage,
    required this.filter,
    required this.itemBuilder,
    this.header,
  });

  final String title;
  final String? actionLabel;
  final VoidCallback? onAction;
  final VoidCallback onRetry;
  final AsyncValue<List<Map<String, dynamic>>> state;
  final String emptyMessage;
  final List<Map<String, dynamic>> Function(List<Map<String, dynamic>>) filter;
  final Widget Function(Map<String, dynamic>) itemBuilder;
  final Widget? header;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
              title: title, actionLabel: actionLabel, onAction: onAction),
          const SizedBox(height: 12),
          if (header != null) ...[
            header!,
            const SizedBox(height: 12),
          ],
          state.when(
            loading: () =>
                const SizedBox(height: 120, child: AsyncStateView.loading()),
            error: (_, __) => AsyncStateView.error(
              'No pudimos cargar $title.',
              actionLabel: 'Reintentar',
              onAction: onRetry,
            ),
            data: (items) {
              final filtered = filter(items);
              return filtered.isEmpty
                  ? AsyncStateView.empty(
                      emptyMessage,
                      title: 'Nada creado todavia',
                      icon: Icons.add_card_rounded,
                      actionLabel: actionLabel,
                      onAction: onAction,
                    )
                  : Column(
                      children: [
                        for (final item in filtered) ...[
                          itemBuilder(item),
                          const SizedBox(height: 10),
                        ],
                      ],
                    );
            },
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
      subtitle: _firstText([card['email'], card['phone_number']],
          fallback: 'Tarjeta digital'),
      icon: Icons.badge_rounded,
      accent: AppColors.blue,
      slug: card['slug']?.toString(),
      onTap: () => context
          .push('/cards/detail', extra: {'kind': 'digital', 'card': card}),
    );
  }
}

class _BusinessCardTile extends StatelessWidget {
  const _BusinessCardTile({required this.card});

  final Map<String, dynamic> card;

  @override
  Widget build(BuildContext context) {
    return _CardTile(
      title: _firstText([card['display_name']],
          fallback: 'Tarjeta de presentacion'),
      subtitle: _firstText([card['company_name'], card['job_title']],
          fallback: 'Presentacion empresarial'),
      icon: Icons.contact_page_rounded,
      accent: AppColors.gold,
      slug: card['slug']?.toString(),
      onTap: () => context
          .push('/cards/detail', extra: {'kind': 'business', 'card': card}),
    );
  }
}

class _PendingDraftCard extends StatelessWidget {
  const _PendingDraftCard({
    required this.draft,
    required this.onContinue,
    required this.onDiscard,
  });

  final BusinessCardDraft draft;
  final VoidCallback onContinue;
  final Future<void> Function() onDiscard;

  @override
  Widget build(BuildContext context) {
    final title = _firstText(
      [draft.displayName, draft.companyName],
      fallback: 'Borrador de tarjeta fisica',
    );
    final subtitle = _firstText(
      [draft.companyName, draft.jobTitle, draft.email],
      fallback: 'Pendiente de publicar en Cardbook',
    );
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: .1),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.gold.withValues(alpha: .45)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(
                  color: AppColors.gold.withValues(alpha: .16),
                  borderRadius: BorderRadius.circular(15),
                ),
                child: const Icon(Icons.pending_actions_rounded,
                    color: AppColors.gold),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const StatusBadge(
                        label: 'Borrador pendiente',
                        icon: Icons.cloud_off_rounded,
                        color: AppColors.gold),
                    const SizedBox(height: 8),
                    Text(title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontWeight: FontWeight.w900)),
                    const SizedBox(height: 3),
                    Text(subtitle,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            color: AppColors.muted, fontSize: 12)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            'Guardado localmente ${_relativeDraftTime(draft.updatedAt)}. Puedes continuar la edicion o publicarlo desde el formulario.',
            style: const TextStyle(
                color: AppColors.muted, fontSize: 12, height: 1.35),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              FilledButton.icon(
                onPressed: onContinue,
                icon: const Icon(Icons.edit_rounded),
                label: const Text('Continuar'),
              ),
              TextButton.icon(
                onPressed: () async => onDiscard(),
                icon: const Icon(Icons.delete_outline_rounded),
                label: const Text('Descartar'),
              ),
            ],
          ),
        ],
      ),
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

String _relativeDraftTime(DateTime updatedAt) {
  final diff = DateTime.now().difference(updatedAt);
  if (diff.inMinutes < 1) return 'hace unos segundos';
  if (diff.inMinutes < 60) return 'hace ${diff.inMinutes} min';
  if (diff.inHours < 24) return 'hace ${diff.inHours} h';
  return 'hace ${diff.inDays} d';
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
          color: AppColors.inkAlt.withValues(alpha: .72),
          borderRadius: BorderRadius.circular(AppRadius.md),
          border: Border.all(color: AppColors.stroke),
        ),
        child: Row(
          children: [
            Container(
              width: 50,
              height: 50,
              decoration: BoxDecoration(
                color: accent.withValues(alpha: .14),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(icon, color: accent),
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
                  Text(subtitle,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                          color: AppColors.muted, fontSize: 12)),
                  if (slug != null && slug!.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(slug!,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            color: AppColors.purple, fontSize: 12)),
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
          StatusBadge(
              label: 'Tarjetas digitales',
              icon: Icons.qr_code_2_rounded,
              color: AppColors.gold),
          SizedBox(height: 16),
          Text('Tarjetas',
              style: TextStyle(
                  fontSize: 32, height: 1.05, fontWeight: FontWeight.w900)),
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
