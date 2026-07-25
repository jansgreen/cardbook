import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/book/data/book_repository.dart';
import 'package:mobile_cardbook/features/home/data/mobile_bootstrap_repository.dart';
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

class BookScreen extends ConsumerStatefulWidget {
  const BookScreen({super.key});

  @override
  ConsumerState<BookScreen> createState() => _BookScreenState();
}

class _BookScreenState extends ConsumerState<BookScreen> {
  final _search = TextEditingController();
  String _filter = 'all';

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final book = ref.watch(mobileBookProvider);
    final accountType =
        ref.watch(mobileBootstrapProvider).valueOrNull?.accountType ?? '';

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(bookProvider);
              ref.invalidate(mobileBookProvider);
              await ref.read(mobileBookProvider.future);
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
              children: [
                const BrandHeader(),
                const SizedBox(height: 24),
                const _BookHero(),
                const SizedBox(height: 18),
                TextField(
                  controller: _search,
                  onChanged: (_) => setState(() {}),
                  decoration: InputDecoration(
                    hintText: 'Buscar en Book por empresa, tarjeta o talento',
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
                const SizedBox(height: 12),
                _BookFilters(
                  selected: _filter,
                  onChanged: (value) => setState(() => _filter = value),
                ),
                const SizedBox(height: 18),
                book.when(
                  loading: () => const SizedBox(
                    height: 220,
                    child: AsyncStateView.loading(),
                  ),
                  error: (_, __) => AsyncStateView.error(
                    'No pudimos cargar tu Book.',
                    actionLabel: 'Reintentar',
                    onAction: () => ref.invalidate(mobileBookProvider),
                  ),
                  data: (data) => _BookContent(
                    data: data,
                    query: _search.text,
                    filter: _filter,
                    accountType: accountType,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: 3),
    );
  }
}

class _BookContent extends StatelessWidget {
  const _BookContent({
    required this.data,
    required this.query,
    required this.filter,
    required this.accountType,
  });

  final Map<String, dynamic> data;
  final String query;
  final String filter;
  final String accountType;

  @override
  Widget build(BuildContext context) {
    final activeCompany = data['active_company'] is Map<String, dynamic>
        ? data['active_company'] as Map<String, dynamic>
        : null;
    final businesses = _filterSavedBusinesses(_list(data['businesses']));
    final savedCandidates = _filterCandidates(_list(data['saved_candidates']));
    final recommendations = _filterCandidates(_list(data['recommendations']));
    final isOffline = data['_offline'] == true;
    final isJob = accountType == 'job';

    return Column(
      children: [
        if (isOffline) ...[
          const OfflineNotice(),
          const SizedBox(height: 18),
        ],
        if (activeCompany != null) ...[
          _ActiveCompanyCard(company: activeCompany),
          const SizedBox(height: 18),
        ],
        if (_showBusinessSection)
          _BookSection(
            title: 'Guardados',
            actionLabel: 'Explorar',
            onAction: () => context.push('/companies'),
            empty: AsyncStateView.empty(
              isJob
                  ? 'Guarda empresas, perfiles y tarjetas que compartan contigo. Este Book es gratis para tu coleccion.'
                  : 'Cuando guardes empresas, perfiles o tarjetas, apareceran aqui.',
              title: 'Tu Book esta listo',
              icon: Icons.bookmark_add_rounded,
              actionLabel: 'Explorar negocios',
              onAction: () => context.push('/companies'),
            ),
            children: [
              for (final item in businesses) ...[
                _BusinessBookTile(item: item),
                const SizedBox(height: 10),
              ],
            ],
          ),
        if (_showBusinessSection && _showCandidatesSection)
          const SizedBox(height: 18),
        if (_showCandidatesSection)
          _BookSection(
            title: 'Candidatos guardados',
            actionLabel: 'Talento',
            onAction: () => context.push('/jobs'),
            empty: AsyncStateView.empty(
              isJob
                  ? 'Aqui veras White Card Jobs guardadas cuando recibas o guardes perfiles laborales.'
                  : 'Los White Card Jobs guardados por tu empresa apareceran aqui.',
              title: 'Sin candidatos guardados',
              icon: Icons.work_outline_rounded,
              actionLabel: 'Ver White Card Jobs',
              onAction: () => context.push('/jobs'),
            ),
            children: [
              for (final item in savedCandidates) ...[
                _SavedCandidateTile(item: item),
                const SizedBox(height: 10),
              ],
            ],
          ),
        if (!isJob && (filter == 'all' || filter == 'candidates')) ...[
          const SizedBox(height: 18),
          _BookSection(
            title: 'Recomendaciones',
            actionLabel: 'Afinidad',
            onAction: () => context.push('/jobs'),
            empty: activeCompany == null
                ? AsyncStateView.empty(
                    'Crea una empresa para recibir candidatos recomendados por afinidad.',
                    title: 'Necesitas una empresa',
                    icon: Icons.business_center_rounded,
                    actionLabel: 'Crear empresa',
                    onAction: () => context.push('/companies/form'),
                  )
                : const AsyncStateView.empty(
                    'Vuelve mas tarde o guarda candidatos desde White Card Jobs.',
                    title: 'Sin recomendaciones todavia',
                    icon: Icons.manage_search_rounded,
                  ),
            children: [
              for (final job in recommendations) ...[
                _RecommendationTile(
                  job: job,
                  companyId: _intValue(activeCompany?['id']),
                ),
                const SizedBox(height: 10),
              ],
            ],
          ),
        ],
      ],
    );
  }

  bool get _showBusinessSection {
    return filter == 'all' ||
        filter == 'companies' ||
        filter == 'digital_cards' ||
        filter == 'business_cards';
  }

  bool get _showCandidatesSection {
    return filter == 'all' || filter == 'candidates';
  }

  List<Map<String, dynamic>> _filterSavedBusinesses(
      List<Map<String, dynamic>> items) {
    return items.where((item) {
      if (filter == 'companies' &&
          (item['company_detail'] == null ||
              item['digital_card_detail'] != null ||
              item['business_card_detail'] != null)) {
        return false;
      }
      if (filter == 'digital_cards' && item['digital_card_detail'] == null) {
        return false;
      }
      if (filter == 'business_cards' && item['business_card_detail'] == null) {
        return false;
      }
      return _matchesBookQuery(item);
    }).toList();
  }

  List<Map<String, dynamic>> _filterCandidates(
      List<Map<String, dynamic>> items) {
    return items.where(_matchesCandidateQuery).toList();
  }

  bool _matchesBookQuery(Map<String, dynamic> item) {
    final q = query.trim().toLowerCase();
    if (q.isEmpty) return true;
    final company = _map(item['company_detail']);
    final digital = _map(item['digital_card_detail']);
    final business = _map(item['business_card_detail']);
    final haystack = [
      item['notes'],
      company['name'],
      company['description'],
      company['category'],
      digital['job_title'],
      digital['email'],
      digital['phone_number'],
      business['display_name'],
      business['company_name'],
      business['job_title'],
      business['email'],
      business['phone_number'],
    ].map((value) => value?.toString().toLowerCase() ?? '').join(' ');
    return haystack.contains(q);
  }

  bool _matchesCandidateQuery(Map<String, dynamic> item) {
    final q = query.trim().toLowerCase();
    if (q.isEmpty) return true;
    final job = item['job_card_detail'] is Map<String, dynamic>
        ? item['job_card_detail'] as Map<String, dynamic>
        : item;
    final specialty = _map(job['specialty_detail']);
    final haystack = [
      job['display_name'],
      job['username'],
      job['title'],
      job['short_description'],
      job['address'],
      job['technologies'],
      specialty['name'],
      specialty['category'],
    ].map((value) => value?.toString().toLowerCase() ?? '').join(' ');
    return haystack.contains(q);
  }
}

class _BookFilters extends StatelessWidget {
  const _BookFilters({required this.selected, required this.onChanged});

  final String selected;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    const filters = [
      ('all', 'Todo'),
      ('companies', 'Empresas'),
      ('digital_cards', 'Perfiles'),
      ('business_cards', 'Tarjetas'),
      ('candidates', 'Candidatos'),
    ];
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          for (final filter in filters) ...[
            ChoiceChip(
              label: Text(filter.$2),
              selected: selected == filter.$1,
              onSelected: (_) => onChanged(filter.$1),
            ),
            const SizedBox(width: 8),
          ],
        ],
      ),
    );
  }
}

class _BookSection extends StatelessWidget {
  const _BookSection({
    required this.title,
    required this.empty,
    required this.children,
    this.actionLabel,
    this.onAction,
  });

  final String title;
  final String? actionLabel;
  final VoidCallback? onAction;
  final Widget empty;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
              title: title, actionLabel: actionLabel, onAction: onAction),
          const SizedBox(height: 12),
          if (children.isEmpty) empty else ...children,
        ],
      ),
    );
  }
}

class _ActiveCompanyCard extends StatelessWidget {
  const _ActiveCompanyCard({required this.company});

  final Map<String, dynamic> company;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      gradient: AppGradients.cardGlow,
      child: Row(
        children: [
          const Icon(Icons.business_center_rounded,
              color: AppColors.gold, size: 34),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Empresa activa',
                    style: TextStyle(color: AppColors.muted, fontSize: 12)),
                const SizedBox(height: 3),
                Text(
                  _text(company['name'], fallback: 'Empresa Cardbook'),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                      fontSize: 18, fontWeight: FontWeight.w900),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _BusinessBookTile extends ConsumerWidget {
  const _BusinessBookTile({required this.item});

  final Map<String, dynamic> item;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final company = item['company_detail'] is Map<String, dynamic>
        ? item['company_detail'] as Map<String, dynamic>
        : <String, dynamic>{};
    final digitalCard = _map(item['digital_card_detail']);
    final businessCard = _map(item['business_card_detail']);
    final notes = _text(item['notes']);
    final isBusinessCard = businessCard.isNotEmpty;
    final isDigitalCard = digitalCard.isNotEmpty && !isBusinessCard;
    final title = isBusinessCard
        ? _text(businessCard['display_name'], fallback: 'Tarjeta guardada')
        : isDigitalCard
            ? _text(company['name'], fallback: 'Perfil guardado')
            : _text(company['name'], fallback: 'Negocio guardado');
    final description = notes.isNotEmpty
        ? notes
        : isBusinessCard
            ? _text(businessCard['company_name'],
                fallback: _text(businessCard['job_title'],
                    fallback: 'Tarjeta de presentacion'))
            : isDigitalCard
                ? _text(digitalCard['job_title'], fallback: 'Perfil de negocio')
                : _text(company['description'], fallback: 'Guardado en Book');
    final iconLabel = isBusinessCard
        ? 'Tarjeta'
        : isDigitalCard
            ? 'Perfil'
            : 'Empresa';
    return Column(
      children: [
        InkWell(
          onTap: () {
            if (isBusinessCard) {
              context.push('/cards/detail',
                  extra: {'kind': 'business', 'card': businessCard});
            } else if (isDigitalCard) {
              context.push('/cards/detail',
                  extra: {'kind': 'digital', 'card': digitalCard});
            } else {
              context.push('/companies/detail', extra: company);
            }
          },
          borderRadius: BorderRadius.circular(AppRadius.md),
          child: Container(
            padding: const EdgeInsets.all(12),
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
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: (isBusinessCard
                            ? AppColors.gold
                            : isDigitalCard
                                ? AppColors.blue
                                : AppColors.purple)
                        .withValues(alpha: .16),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Icon(
                    isBusinessCard
                        ? Icons.contact_page_rounded
                        : isDigitalCard
                            ? Icons.badge_rounded
                            : Icons.business_center_rounded,
                    color: isBusinessCard
                        ? AppColors.gold
                        : isDigitalCard
                            ? AppColors.blue
                            : AppColors.purple,
                  ),
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
                      Text(description,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                              color: AppColors.muted, fontSize: 12)),
                      const SizedBox(height: 6),
                      Text(iconLabel,
                          style: const TextStyle(
                              color: AppColors.gold,
                              fontWeight: FontWeight.w800,
                              fontSize: 12)),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right_rounded, color: AppColors.muted),
              ],
            ),
          ),
        ),
        const SizedBox(height: 8),
        Align(
          alignment: Alignment.centerRight,
          child: TextButton.icon(
            onPressed: () => _remove(context, ref),
            icon: const Icon(Icons.delete_outline_rounded,
                size: 18, color: AppColors.red),
            label: const Text('Quitar de Book',
                style: TextStyle(color: AppColors.red)),
          ),
        ),
      ],
    );
  }

  Future<void> _remove(BuildContext context, WidgetRef ref) async {
    final id = _intValue(item['id']);
    if (id == null) return;
    try {
      await ref.read(bookRepositoryProvider).remove(id);
      _refreshBook(ref);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Quitado de Book.')),
        );
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No pudimos quitar este guardado.')),
        );
      }
    }
  }
}

class _SavedCandidateTile extends ConsumerWidget {
  const _SavedCandidateTile({required this.item});

  final Map<String, dynamic> item;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final job = item['job_card_detail'] is Map<String, dynamic>
        ? item['job_card_detail'] as Map<String, dynamic>
        : <String, dynamic>{};
    return _CandidateTile(
      job: job,
      trailing: TextButton.icon(
        onPressed: () => _remove(context, ref),
        icon: const Icon(Icons.delete_outline_rounded,
            size: 18, color: AppColors.red),
        label: const Text('Quitar', style: TextStyle(color: AppColors.red)),
      ),
    );
  }

  Future<void> _remove(BuildContext context, WidgetRef ref) async {
    final id = _intValue(item['id']);
    if (id == null) return;
    try {
      await ref.read(bookRepositoryProvider).removeCandidate(id);
      _refreshBook(ref);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Candidato quitado de Book.')),
        );
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No pudimos quitar este candidato.')),
        );
      }
    }
  }
}

class _RecommendationTile extends ConsumerWidget {
  const _RecommendationTile({required this.job, required this.companyId});

  final Map<String, dynamic> job;
  final int? companyId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return _CandidateTile(
      job: job,
      trailing: TextButton.icon(
        onPressed: companyId == null ? null : () => _save(context, ref),
        icon: const Icon(Icons.bookmark_add_rounded, size: 18),
        label: const Text('Guardar'),
      ),
    );
  }

  Future<void> _save(BuildContext context, WidgetRef ref) async {
    final jobId = _intValue(job['id']);
    if (companyId == null || jobId == null) return;
    try {
      await ref
          .read(bookRepositoryProvider)
          .saveCandidate(companyId: companyId!, jobCardId: jobId);
      _refreshBook(ref);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Candidato guardado en Book.')),
        );
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No pudimos guardar este candidato.')),
        );
      }
    }
  }
}

class _CandidateTile extends StatelessWidget {
  const _CandidateTile({required this.job, required this.trailing});

  final Map<String, dynamic> job;
  final Widget trailing;

  @override
  Widget build(BuildContext context) {
    final specialty = job['specialty_detail'] is Map<String, dynamic>
        ? job['specialty_detail'] as Map<String, dynamic>
        : <String, dynamic>{};
    final title = _text(job['title'],
        fallback: _text(specialty['name'], fallback: 'White Card Job'));
    final name = _text(job['display_name'],
        fallback: _text(job['username'], fallback: 'Candidato'));
    final description = _text(job['short_description'],
        fallback: _text(specialty['category'],
            fallback: 'Disponible para nuevas oportunidades.'));
    final photo = _text(job['photo']);
    final publicUrl = _text(job['public_url']);
    final phone = _text(job['phone_number']);
    final email = _text(job['email']);

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.inkAlt.withValues(alpha: .72),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.stroke),
      ),
      child: Column(
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: Colors.white,
                backgroundImage: photo.isEmpty ? null : NetworkImage(photo),
                child: photo.isEmpty
                    ? Text(_initials(name),
                        style: const TextStyle(
                            color: AppColors.ink, fontWeight: FontWeight.w900))
                    : null,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(name,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontWeight: FontWeight.w900)),
                    const SizedBox(height: 3),
                    Text(title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            color: AppColors.gold,
                            fontWeight: FontWeight.w800)),
                    const SizedBox(height: 3),
                    Text(description,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            color: AppColors.muted, fontSize: 12)),
                  ],
                ),
              ),
              IconButton(
                onPressed: publicUrl.isEmpty
                    ? null
                    : () => ShareCenter.show(
                          context,
                          SharePayload(
                            type: ShareTargetType.whiteCardJob,
                            title: name,
                            subtitle: title,
                            url: publicUrl,
                            phone: phone,
                            email: email,
                            jobTitle: title,
                          ),
                        ),
                icon:
                    const Icon(Icons.ios_share_rounded, color: AppColors.text),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Align(alignment: Alignment.centerRight, child: trailing),
        ],
      ),
    );
  }
}

class _BookHero extends StatelessWidget {
  const _BookHero();

  @override
  Widget build(BuildContext context) {
    return const GlassCard(
      gradient: AppGradients.cardGlow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          StatusBadge(
              label: 'Coleccion empresarial',
              icon: Icons.bookmarks_rounded,
              color: AppColors.gold),
          SizedBox(height: 16),
          Text('Book',
              style: TextStyle(
                  fontSize: 32, height: 1.05, fontWeight: FontWeight.w900)),
          SizedBox(height: 8),
          Text(
            'Tus empresas, tarjetas, perfiles y candidatos guardados en un solo lugar.',
            style: TextStyle(color: AppColors.muted, height: 1.45),
          ),
        ],
      ),
    );
  }
}

List<Map<String, dynamic>> _list(dynamic value) {
  return (value as List<dynamic>? ?? [])
      .whereType<Map<String, dynamic>>()
      .toList();
}

Map<String, dynamic> _map(dynamic value) {
  return value is Map<String, dynamic> ? value : <String, dynamic>{};
}

String _text(dynamic value, {String fallback = ''}) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
}

int? _intValue(dynamic value) {
  if (value is int) return value;
  return int.tryParse(value?.toString() ?? '');
}

String _initials(String value) {
  final words = value
      .trim()
      .split(RegExp(r'\s+'))
      .where((word) => word.isNotEmpty)
      .toList();
  if (words.isEmpty) {
    return 'CB';
  }
  if (words.length == 1) {
    return words.first
        .substring(0, words.first.length >= 2 ? 2 : 1)
        .toUpperCase();
  }
  return '${words[0][0]}${words[1][0]}'.toUpperCase();
}

void _refreshBook(WidgetRef ref) {
  ref.invalidate(bookProvider);
  ref.invalidate(mobileBookProvider);
}
