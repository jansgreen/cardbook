import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/book/data/book_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/company_tile.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/offline_notice.dart';
import 'package:mobile_cardbook/shared/widgets/section_header.dart';
import 'package:mobile_cardbook/shared/widgets/share_center.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class BookScreen extends ConsumerWidget {
  const BookScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final book = ref.watch(mobileBookProvider);

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
                  data: (data) => _BookContent(data: data),
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
  const _BookContent({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final activeCompany = data['active_company'] is Map<String, dynamic>
        ? data['active_company'] as Map<String, dynamic>
        : null;
    final businesses = _list(data['businesses']);
    final savedCandidates = _list(data['saved_candidates']);
    final recommendations = _list(data['recommendations']);
    final isOffline = data['_offline'] == true;

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
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionHeader(
                  title: 'Negocios guardados', actionLabel: 'Book'),
              const SizedBox(height: 12),
              if (businesses.isEmpty)
                AsyncStateView.empty(
                  'Cuando guardes empresas, perfiles o tarjetas, apareceran aqui.',
                  title: 'Tu Book esta listo',
                  icon: Icons.bookmark_add_rounded,
                  actionLabel: 'Explorar negocios',
                  onAction: () => context.push('/marketplace'),
                )
              else
                for (final item in businesses) ...[
                  _BusinessBookTile(item: item),
                  const SizedBox(height: 10),
                ],
            ],
          ),
        ),
        const SizedBox(height: 18),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionHeader(
                  title: 'Candidatos guardados', actionLabel: 'Talento'),
              const SizedBox(height: 12),
              if (savedCandidates.isEmpty)
                AsyncStateView.empty(
                  'Los White Card Jobs guardados por tu empresa apareceran aqui.',
                  title: 'Sin candidatos guardados',
                  icon: Icons.work_outline_rounded,
                  actionLabel: 'Ver White Card Jobs',
                  onAction: () => context.push('/jobs'),
                )
              else
                for (final item in savedCandidates) ...[
                  _SavedCandidateTile(item: item),
                  const SizedBox(height: 10),
                ],
            ],
          ),
        ),
        const SizedBox(height: 18),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionHeader(
                  title: 'Recomendaciones', actionLabel: 'Afinidad'),
              const SizedBox(height: 12),
              if (activeCompany == null)
                AsyncStateView.empty(
                  'Crea una empresa para recibir candidatos recomendados por afinidad.',
                  title: 'Necesitas una empresa',
                  icon: Icons.business_center_rounded,
                  actionLabel: 'Crear empresa',
                  onAction: () => context.push('/companies/form'),
                )
              else if (recommendations.isEmpty)
                const AsyncStateView.empty(
                  'Vuelve mas tarde o guarda candidatos desde White Card Jobs.',
                  title: 'Sin recomendaciones todavia',
                  icon: Icons.manage_search_rounded,
                )
              else
                for (final job in recommendations) ...[
                  _RecommendationTile(
                    job: job,
                    companyId: _intValue(activeCompany['id']),
                  ),
                  const SizedBox(height: 10),
                ],
            ],
          ),
        ),
      ],
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
    final notes = _text(item['notes']);
    return Column(
      children: [
        CompanyTile(
          name: _text(company['name'], fallback: 'Negocio guardado'),
          description: notes.isNotEmpty
              ? notes
              : _text(company['description'], fallback: 'Guardado en Book'),
          rating: _compactNumber(company['efficient_count']),
          logoUrl: company['logo']?.toString(),
          onTap: () => context.push('/companies/detail', extra: company),
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

String _text(dynamic value, {String fallback = ''}) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
}

int? _intValue(dynamic value) {
  if (value is int) return value;
  return int.tryParse(value?.toString() ?? '');
}

String _compactNumber(dynamic value) {
  final number =
      value is num ? value : num.tryParse(value?.toString() ?? '') ?? 0;
  if (number >= 1000) return '${(number / 1000).toStringAsFixed(1)}k';
  return number.toInt().toString();
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
