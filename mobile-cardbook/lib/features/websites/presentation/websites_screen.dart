import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/platform/native_actions.dart';
import 'package:mobile_cardbook/features/home/data/mobile_bootstrap_repository.dart';
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

class WebsitesScreen extends ConsumerStatefulWidget {
  const WebsitesScreen({super.key});

  @override
  ConsumerState<WebsitesScreen> createState() => _WebsitesScreenState();
}

class _WebsitesScreenState extends ConsumerState<WebsitesScreen> {
  final _search = TextEditingController();

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final payload = ref.watch(mobileWebsitesPayloadProvider);
    final bootstrap = ref.watch(mobileBootstrapProvider).valueOrNull;
    final canManage = bootstrap?.can('can_manage_website') ?? false;

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(mobileWebsitesPayloadProvider);
              ref.invalidate(mobileWebsitesProvider);
              await ref.read(mobileWebsitesPayloadProvider.future);
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
              children: [
                const BrandHeader(),
                const SizedBox(height: 24),
                _WebsitesHero(canManage: canManage),
                const SizedBox(height: 18),
                _WebsiteSearch(
                  controller: _search,
                  onChanged: (_) => setState(() {}),
                ),
                const SizedBox(height: 18),
                payload.when(
                  loading: () => const SizedBox(
                      height: 260, child: AsyncStateView.loading()),
                  error: (_, __) => AsyncStateView.error(
                    'No pudimos cargar tus websites.',
                    actionLabel: 'Reintentar',
                    onAction: () =>
                        ref.invalidate(mobileWebsitesPayloadProvider),
                  ),
                  data: (data) {
                    final websites = _filter(data.websites);
                    final publishedCount = data.websites
                        .where((item) => item['is_published'] == true)
                        .length;
                    return Column(
                      children: [
                        _BuilderSummary(
                          total: data.websites.length,
                          published: publishedCount,
                          draft: data.websites.length - publishedCount,
                          builderHome: data.builderHome,
                          canManage: canManage,
                        ),
                        const SizedBox(height: 18),
                        GlassCard(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              SectionHeader(
                                title: 'Websites',
                                actionLabel: canManage ? 'Builder' : null,
                                onAction: canManage &&
                                        data.builderHome.isNotEmpty
                                    ? () =>
                                        NativeActions.website(data.builderHome)
                                    : null,
                              ),
                              const SizedBox(height: 12),
                              if (websites.isEmpty)
                                AsyncStateView.empty(
                                  data.websites.isEmpty
                                      ? 'Cuando actives Website Builder, tus sitios apareceran aqui.'
                                      : 'No hay websites que coincidan con tu busqueda.',
                                  title: data.websites.isEmpty
                                      ? 'Sin websites'
                                      : 'Sin resultados',
                                  icon: Icons.language_rounded,
                                  actionLabel:
                                      canManage ? 'Abrir builder' : null,
                                  onAction:
                                      canManage && data.builderHome.isNotEmpty
                                          ? () => NativeActions.website(
                                              data.builderHome)
                                          : null,
                                )
                              else
                                Column(
                                  children: [
                                    for (final website in websites) ...[
                                      _WebsiteTile(
                                        website: website,
                                        canManageGlobal: canManage,
                                      ),
                                      const SizedBox(height: 12),
                                    ],
                                  ],
                                ),
                            ],
                          ),
                        ),
                      ],
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: null),
    );
  }

  List<Map<String, dynamic>> _filter(List<Map<String, dynamic>> websites) {
    final query = _search.text.trim().toLowerCase();
    if (query.isEmpty) return websites;
    return websites.where((website) {
      final haystack = [
        website['title'],
        website['company_name'],
        website['slug'],
        website['domain'],
        website['subdomain'],
      ].map(_text).join(' ').toLowerCase();
      return haystack.contains(query);
    }).toList();
  }
}

class _BuilderSummary extends StatelessWidget {
  const _BuilderSummary({
    required this.total,
    required this.published,
    required this.draft,
    required this.builderHome,
    required this.canManage,
  });

  final int total;
  final int published;
  final int draft;
  final String builderHome;
  final bool canManage;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(title: 'Control del builder'),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: _MetricPill(
                  label: 'Sitios',
                  value: total.toString(),
                  icon: Icons.language_rounded,
                  color: AppColors.cyan,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _MetricPill(
                  label: 'Publicados',
                  value: published.toString(),
                  icon: Icons.verified_rounded,
                  color: AppColors.green,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _MetricPill(
                  label: 'Borrador',
                  value: draft.toString(),
                  icon: Icons.edit_note_rounded,
                  color: AppColors.gold,
                ),
              ),
            ],
          ),
          if (canManage && builderHome.isNotEmpty) ...[
            const SizedBox(height: 14),
            FilledButton.icon(
              onPressed: () => NativeActions.website(builderHome),
              icon: const Icon(Icons.tune_rounded),
              label: const Text('Administrar websites'),
            ),
          ],
        ],
      ),
    );
  }
}

class _MetricPill extends StatelessWidget {
  const _MetricPill({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  final String label;
  final String value;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: .1),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: color.withValues(alpha: .26)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 8),
          Text(value,
              style:
                  const TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
          Text(label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: AppColors.muted, fontSize: 11)),
        ],
      ),
    );
  }
}

class _WebsiteTile extends StatelessWidget {
  const _WebsiteTile({
    required this.website,
    required this.canManageGlobal,
  });

  final Map<String, dynamic> website;
  final bool canManageGlobal;

  @override
  Widget build(BuildContext context) {
    final title = _text(website['title'], fallback: 'Website Cardbook');
    final companyName = _text(website['company_name'], fallback: 'Empresa');
    final url = _text(website['public_url']);
    final builderUrl = _text(website['builder_url']);
    final published = website['is_published'] == true;
    final canManage = canManageGlobal && website['can_manage'] == true;
    final status = website['publish_status'] is Map<String, dynamic>
        ? website['publish_status'] as Map<String, dynamic>
        : const <String, dynamic>{};
    final issues = (status['issues'] as List<dynamic>? ?? [])
        .map((item) => item.toString())
        .toList();
    final pages = _items(website['pages']);
    final pageCount = _int(website['page_count']);
    final publishedPages = _int(website['published_page_count']);
    final sectionCount = _int(website['section_count']);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.inkAlt.withValues(alpha: .72),
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(
          color: published
              ? AppColors.green.withValues(alpha: .32)
              : AppColors.gold.withValues(alpha: .32),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(18),
                  gradient: LinearGradient(colors: [
                    Color(_color(website['primary_color'])),
                    Color(_color(website['accent_color'])),
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
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            fontSize: 17, fontWeight: FontWeight.w900)),
                    const SizedBox(height: 4),
                    Text(companyName,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            color: AppColors.muted, fontSize: 12)),
                  ],
                ),
              ),
              StatusBadge(
                label: published ? 'Publicado' : 'Borrador',
                icon: published
                    ? Icons.verified_rounded
                    : Icons.pending_actions_rounded,
                color: published ? AppColors.green : AppColors.gold,
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                  child: _TinyStat(
                      label: 'Paginas', value: '$publishedPages/$pageCount')),
              const SizedBox(width: 8),
              Expanded(
                  child: _TinyStat(label: 'Secciones', value: '$sectionCount')),
              const SizedBox(width: 8),
              Expanded(
                  child: _TinyStat(
                      label: 'HTML5',
                      value: pages.isEmpty ? 'Base' : 'Activo')),
            ],
          ),
          if (pages.isNotEmpty) ...[
            const SizedBox(height: 14),
            _PagesPreview(pages: pages),
          ],
          if (issues.isNotEmpty) ...[
            const SizedBox(height: 14),
            _IssuesList(issues: issues),
          ],
          const SizedBox(height: 14),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              _ActionChipButton(
                label: 'Preview',
                icon: Icons.visibility_rounded,
                enabled: url.isNotEmpty,
                onTap: () => NativeActions.website(url),
              ),
              _ActionChipButton(
                label: 'Compartir',
                icon: Icons.ios_share_rounded,
                enabled: url.isNotEmpty,
                onTap: () => ShareCenter.show(
                  context,
                  SharePayload(
                    type: ShareTargetType.website,
                    title: title,
                    subtitle: companyName,
                    url: url,
                    website: url,
                  ),
                ),
              ),
              _ActionChipButton(
                label: 'Editar',
                icon: Icons.design_services_rounded,
                enabled: canManage && builderUrl.isNotEmpty,
                highlighted: true,
                onTap: () => NativeActions.website(builderUrl),
              ),
            ],
          ),
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

class _TinyStat extends StatelessWidget {
  const _TinyStat({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
      decoration: BoxDecoration(
        color: AppColors.panelSoft.withValues(alpha: .72),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.stroke),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(value,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontWeight: FontWeight.w900)),
          Text(label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: AppColors.muted, fontSize: 10)),
        ],
      ),
    );
  }
}

class _PagesPreview extends StatelessWidget {
  const _PagesPreview({required this.pages});

  final List<Map<String, dynamic>> pages;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Estructura publica',
            style: TextStyle(fontWeight: FontWeight.w900, fontSize: 13)),
        const SizedBox(height: 8),
        for (final page in pages.take(4)) ...[
          Row(
            children: [
              Icon(
                page['is_homepage'] == true
                    ? Icons.home_work_rounded
                    : Icons.description_rounded,
                color: page['is_published'] == true
                    ? AppColors.green
                    : AppColors.gold,
                size: 18,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  _text(page['title'], fallback: 'Pagina'),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
              ),
              Text(
                '${_int(page['section_count'])} secc.',
                style: const TextStyle(color: AppColors.muted, fontSize: 11),
              ),
            ],
          ),
          const SizedBox(height: 7),
        ],
      ],
    );
  }
}

class _IssuesList extends StatelessWidget {
  const _IssuesList({required this.issues});

  final List<String> issues;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: .1),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.gold.withValues(alpha: .28)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Pendiente para publicar',
              style: TextStyle(
                  color: AppColors.gold, fontWeight: FontWeight.w900)),
          const SizedBox(height: 6),
          for (final issue in issues.take(3))
            Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Text(issue,
                  style: const TextStyle(color: AppColors.muted, fontSize: 12)),
            ),
        ],
      ),
    );
  }
}

class _ActionChipButton extends StatelessWidget {
  const _ActionChipButton({
    required this.label,
    required this.icon,
    required this.onTap,
    this.enabled = true,
    this.highlighted = false,
  });

  final String label;
  final IconData icon;
  final VoidCallback onTap;
  final bool enabled;
  final bool highlighted;

  @override
  Widget build(BuildContext context) {
    final color = highlighted ? AppColors.purple : AppColors.text;
    return InkWell(
      onTap: enabled ? onTap : null,
      borderRadius: BorderRadius.circular(999),
      child: Opacity(
        opacity: enabled ? 1 : .42,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 10),
          decoration: BoxDecoration(
            color: highlighted
                ? AppColors.purple.withValues(alpha: .2)
                : AppColors.panelSoft.withValues(alpha: .75),
            borderRadius: BorderRadius.circular(999),
            border: Border.all(color: color.withValues(alpha: .28)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 16, color: color),
              const SizedBox(width: 6),
              Text(label,
                  style: TextStyle(color: color, fontWeight: FontWeight.w900)),
            ],
          ),
        ),
      ),
    );
  }
}

class _WebsiteSearch extends StatelessWidget {
  const _WebsiteSearch({required this.controller, required this.onChanged});

  final TextEditingController controller;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      onChanged: onChanged,
      decoration: const InputDecoration(
        hintText: 'Buscar website, empresa o dominio',
        prefixIcon: Icon(Icons.search_rounded),
      ),
    );
  }
}

class _WebsitesHero extends StatelessWidget {
  const _WebsitesHero({required this.canManage});

  final bool canManage;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      gradient: AppGradients.cardGlow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          StatusBadge(
            label: canManage ? 'Builder habilitado' : 'Vista de websites',
            icon: Icons.language_rounded,
            color: canManage ? AppColors.green : AppColors.gold,
          ),
          const SizedBox(height: 16),
          const Text('Website Builder',
              style: TextStyle(
                  fontSize: 32, height: 1.05, fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          const Text(
            'Administra la presencia publica de tus empresas, revisa paginas y abre la vista externa desde la app movil.',
            style: TextStyle(color: AppColors.muted, height: 1.45),
          ),
        ],
      ),
    );
  }
}

List<Map<String, dynamic>> _items(dynamic value) {
  if (value is! List) return const <Map<String, dynamic>>[];
  return value.whereType<Map<String, dynamic>>().toList();
}

String _text(dynamic value, {String fallback = ''}) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
}

int _int(dynamic value) {
  if (value is int) return value;
  return int.tryParse(value?.toString() ?? '') ?? 0;
}

int _color(dynamic value) {
  final raw = _text(value, fallback: '#3B36FF').replaceFirst('#', '');
  return int.tryParse('0xFF$raw') ?? 0xFF3B36FF;
}
