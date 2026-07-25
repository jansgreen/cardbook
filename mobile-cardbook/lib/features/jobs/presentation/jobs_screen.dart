import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/core/platform/native_actions.dart';
import 'package:mobile_cardbook/features/jobs/data/job_card_draft_store.dart';
import 'package:mobile_cardbook/features/jobs/data/jobs_repository.dart';
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

class JobsScreen extends ConsumerStatefulWidget {
  const JobsScreen({super.key});

  @override
  ConsumerState<JobsScreen> createState() => _JobsScreenState();
}

class _JobsScreenState extends ConsumerState<JobsScreen> {
  final _search = TextEditingController();

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final jobs = ref.watch(mobileJobsProvider);
    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(mobileJobsProvider);
              ref.invalidate(jobCardDraftProvider);
              await ref.read(mobileJobsProvider.future);
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
              children: [
                const BrandHeader(),
                const SizedBox(height: 24),
                const _JobsHero(),
                const SizedBox(height: 18),
                TextField(
                  controller: _search,
                  onChanged: (_) => setState(() {}),
                  decoration: InputDecoration(
                    hintText: 'Buscar candidato, oficio, ciudad o habilidad',
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
                jobs.when(
                  loading: () => const SizedBox(
                      height: 220, child: AsyncStateView.loading()),
                  error: (_, __) => AsyncStateView.error(
                    'No pudimos cargar las White Card Jobs.',
                    actionLabel: 'Reintentar',
                    onAction: () => ref.invalidate(mobileJobsProvider),
                  ),
                  data: (data) => _JobsContent(
                    data: data,
                    query: _search.text,
                  ),
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

class _JobsContent extends ConsumerWidget {
  const _JobsContent({required this.data, required this.query});

  final Map<String, dynamic> data;
  final String query;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final myCard = data['my_card'] is Map<String, dynamic>
        ? data['my_card'] as Map<String, dynamic>
        : null;
    final available = _filterJobs(
        (data['available_jobs'] as List<dynamic>? ?? [])
            .whereType<Map<String, dynamic>>()
            .toList());
    final recommended = _filterJobs(
        (data['recommended_for_company'] as List<dynamic>? ?? [])
            .whereType<Map<String, dynamic>>()
            .toList());
    final isOffline = data['_offline'] == true;
    final draftState = ref.watch(jobCardDraftProvider);
    return Column(
      children: [
        if (isOffline) ...[
          const OfflineNotice(),
          const SizedBox(height: 18),
        ],
        if (myCard == null) ...[
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SectionHeader(
                    title: 'Mi White Card', actionLabel: 'Crear'),
                const SizedBox(height: 10),
                draftState.when(
                  data: (draft) => draft == null
                      ? const SizedBox.shrink()
                      : _PendingJobDraftCard(
                          draft: draft,
                          onContinue: () => context.push('/jobs/form'),
                          onDiscard: () async {
                            await ref.read(jobCardDraftStoreProvider).clear();
                            ref.invalidate(jobCardDraftProvider);
                          },
                        ),
                  loading: () => const SizedBox.shrink(),
                  error: (_, __) => const SizedBox.shrink(),
                ),
                if (draftState.valueOrNull != null) const SizedBox(height: 12),
                AsyncStateView.empty(
                  'Crea tu tarjeta blanca para aparecer en busquedas de talento.',
                  title: 'Presenta tu perfil laboral',
                  icon: Icons.badge_rounded,
                  actionLabel: 'Crear White Card',
                  onAction: () => context.push('/jobs/form'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 18),
        ] else ...[
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SectionHeader(
                  title: 'Mi White Card',
                  actionLabel:
                      _text(myCard['public_url']).isEmpty ? null : 'Compartir',
                  onAction: _text(myCard['public_url']).isEmpty
                      ? null
                      : () => ShareCenter.show(
                            context,
                            SharePayload(
                              type: ShareTargetType.whiteCardJob,
                              title: _text(myCard['display_name'],
                                  fallback: _text(myCard['username'],
                                      fallback: 'White Card Job')),
                              subtitle: _text(myCard['title'],
                                  fallback: 'Perfil laboral'),
                              url: _text(myCard['public_url']),
                              phone: _text(myCard['phone_number']),
                              email: _text(myCard['email']),
                              jobTitle: _text(myCard['title']),
                            ),
                          ),
                ),
                const SizedBox(height: 12),
                _JobTile(job: myCard, highlighted: true),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () =>
                            context.push('/jobs/form', extra: myCard),
                        icon: const Icon(Icons.edit_rounded),
                        label: const Text('Editar'),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => _confirmDelete(context, ref),
                        icon: const Icon(Icons.delete_outline_rounded),
                        label: const Text('Desactivar'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 18),
        ],
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionHeader(
                  title: 'Recomendados', actionLabel: 'Afinidad'),
              const SizedBox(height: 12),
              if (recommended.isEmpty)
                const AsyncStateView.empty(
                  'Cuando una empresa busque talento, veras recomendaciones aqui.',
                  title: 'Sin recomendaciones todavia',
                  icon: Icons.manage_search_rounded,
                )
              else
                for (final job in recommended.take(5)) ...[
                  _JobTile(job: job),
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
                  title: 'Buscan trabajo', actionLabel: 'Explorar'),
              const SizedBox(height: 12),
              if (available.isEmpty)
                const AsyncStateView.empty(
                  'No hay White Card Jobs disponibles ahora.',
                  title: 'Talento no disponible',
                  icon: Icons.work_off_rounded,
                )
              else
                for (final job in available.take(12)) ...[
                  _JobTile(job: job),
                  const SizedBox(height: 10),
                ],
            ],
          ),
        ),
      ],
    );
  }

  List<Map<String, dynamic>> _filterJobs(List<Map<String, dynamic>> items) {
    final q = query.trim().toLowerCase();
    if (q.isEmpty) return items;
    return items.where((job) {
      final specialty = job['specialty_detail'] is Map<String, dynamic>
          ? job['specialty_detail'] as Map<String, dynamic>
          : const <String, dynamic>{};
      final haystack = [
        job['display_name'],
        job['username'],
        job['title'],
        job['short_description'],
        job['address'],
        job['technologies'],
        job['languages'],
        specialty['name'],
        specialty['category'],
      ].map((value) => value?.toString().toLowerCase() ?? '').join(' ');
      return haystack.contains(q);
    }).toList();
  }

  Future<void> _confirmDelete(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Desactivar White Card'),
            content: const Text(
                'Tu tarjeta dejara de mostrarse en busquedas publicas. Puedes crear una nueva mas adelante.'),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(false),
                child: const Text('Cancelar'),
              ),
              FilledButton(
                onPressed: () => Navigator.of(context).pop(true),
                child: const Text('Desactivar'),
              ),
            ],
          ),
        ) ??
        false;
    if (!context.mounted || !confirmed) return;
    await ref.read(jobRepositoryProvider).deleteMine();
    ref.invalidate(mobileJobsProvider);
  }
}

class _PendingJobDraftCard extends StatelessWidget {
  const _PendingJobDraftCard({
    required this.draft,
    required this.onContinue,
    required this.onDiscard,
  });

  final JobCardDraft draft;
  final VoidCallback onContinue;
  final Future<void> Function() onDiscard;

  @override
  Widget build(BuildContext context) {
    final title = _text(draft.title, fallback: 'Borrador de White Card');
    final subtitle = _text(
      draft.description,
      fallback: 'Pendiente de completar y publicar',
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
                      label: 'Borrador laboral',
                      icon: Icons.cloud_off_rounded,
                      color: AppColors.gold,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w900),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      subtitle,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style:
                          const TextStyle(color: AppColors.muted, fontSize: 12),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            'Guardado localmente ${_relativeDraftTime(draft.updatedAt)}.',
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

class _JobTile extends StatelessWidget {
  const _JobTile({required this.job, this.highlighted = false});

  final Map<String, dynamic> job;
  final bool highlighted;

  @override
  Widget build(BuildContext context) {
    final specialty = job['specialty_detail'] is Map<String, dynamic>
        ? job['specialty_detail'] as Map<String, dynamic>
        : {};
    final title = _text(job['title'],
        fallback: _text(specialty['name'], fallback: 'White Card Job'));
    final name = _text(job['display_name'],
        fallback: _text(job['username'], fallback: 'Candidato'));
    final description = _text(job['short_description'],
        fallback: _text(specialty['category'],
            fallback: 'Disponible para nuevas oportunidades.'));
    final publicUrl = _text(job['public_url']);
    final phone = _text(job['phone_number']);
    final email = _text(job['email']);
    final imported = job['is_physical_card_imported'] == true ||
        _text(job['physical_card_front_image']).isNotEmpty ||
        _text(job['physical_card_back_image']).isNotEmpty;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: highlighted
            ? AppColors.blue.withValues(alpha: .22)
            : AppColors.inkAlt.withValues(alpha: .72),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(
            color: highlighted
                ? AppColors.blue.withValues(alpha: .42)
                : AppColors.stroke),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 24,
            backgroundColor: Colors.white,
            backgroundImage: _text(job['photo']).isEmpty
                ? null
                : NetworkImage(_text(job['photo'])),
            child: _text(job['photo']).isEmpty
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
                        color: AppColors.gold, fontWeight: FontWeight.w800)),
                const SizedBox(height: 3),
                Text(description,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style:
                        const TextStyle(color: AppColors.muted, fontSize: 12)),
                if (imported) ...[
                  const SizedBox(height: 8),
                  const StatusBadge(
                    label: 'Tarjeta fisica importada',
                    icon: Icons.document_scanner_rounded,
                    color: AppColors.gold,
                  ),
                ],
              ],
            ),
          ),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              IconButton(
                tooltip: 'Compartir',
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
              if (imported)
                IconButton(
                  tooltip: 'Ver tarjeta fisica',
                  onPressed: () => _showImportedJobCard(context, job),
                  icon: const Icon(Icons.document_scanner_rounded,
                      color: AppColors.gold),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

void _showImportedJobCard(BuildContext context, Map<String, dynamic> job) {
  final front = _text(job['physical_card_front_image']);
  final back = _text(job['physical_card_back_image']);
  final name = _text(job['display_name'],
      fallback: _text(job['username'], fallback: 'White Card'));
  final publicUrl = _text(job['public_url']);
  showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: AppColors.panel,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
    ),
    builder: (sheetContext) {
      return SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 14, 20, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.document_scanner_rounded,
                      color: AppColors.gold),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'Tarjeta fisica importada',
                      style:
                          TextStyle(fontSize: 18, fontWeight: FontWeight.w900),
                    ),
                  ),
                  IconButton(
                    onPressed: () => Navigator.of(sheetContext).pop(),
                    icon: const Icon(Icons.close_rounded),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                name,
                style: const TextStyle(color: AppColors.muted),
              ),
              if (publicUrl.isNotEmpty) ...[
                const SizedBox(height: 14),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    FilledButton.icon(
                      onPressed: () => NativeActions.shareText(
                        name,
                        'Mira mi White Card Job en Cardbook: $publicUrl',
                      ),
                      icon: const Icon(Icons.ios_share_rounded),
                      label: const Text('Compartir perfil'),
                    ),
                    OutlinedButton.icon(
                      onPressed: () async {
                        await NativeActions.copyText(publicUrl);
                        if (!sheetContext.mounted) return;
                        ScaffoldMessenger.of(sheetContext).showSnackBar(
                          const SnackBar(content: Text('Enlace copiado.')),
                        );
                      },
                      icon: const Icon(Icons.copy_rounded),
                      label: const Text('Copiar enlace'),
                    ),
                  ],
                ),
              ],
              const SizedBox(height: 16),
              _ImportedJobScanPreview(label: 'Frente', url: front),
              if (back.isNotEmpty) ...[
                const SizedBox(height: 12),
                _ImportedJobScanPreview(label: 'Reverso', url: back),
              ],
            ],
          ),
        ),
      );
    },
  );
}

class _ImportedJobScanPreview extends StatelessWidget {
  const _ImportedJobScanPreview({required this.label, required this.url});

  final String label;
  final String url;

  @override
  Widget build(BuildContext context) {
    if (url.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w900),
        ),
        const SizedBox(height: 8),
        AspectRatio(
          aspectRatio: 1.75,
          child: InkWell(
            onTap: () => _showFullImage(context, label: label, url: url),
            borderRadius: BorderRadius.circular(AppRadius.md),
            child: Container(
              clipBehavior: Clip.antiAlias,
              decoration: BoxDecoration(
                color: AppColors.panelSoft,
                borderRadius: BorderRadius.circular(AppRadius.md),
                border: Border.all(color: AppColors.stroke),
              ),
              child: Stack(
                fit: StackFit.expand,
                children: [
                  Image.network(url, fit: BoxFit.cover),
                  Align(
                    alignment: Alignment.bottomRight,
                    child: Container(
                      margin: const EdgeInsets.all(10),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: AppColors.ink.withValues(alpha: .72),
                        borderRadius: BorderRadius.circular(999),
                        border: Border.all(color: AppColors.stroke),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.zoom_out_map_rounded,
                              size: 14, color: AppColors.text),
                          SizedBox(width: 5),
                          Text(
                            'Ampliar',
                            style: TextStyle(
                                fontSize: 11, fontWeight: FontWeight.w800),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

void _showFullImage(BuildContext context,
    {required String label, required String url}) {
  showDialog<void>(
    context: context,
    builder: (dialogContext) {
      return Dialog(
        backgroundColor: AppColors.ink,
        insetPadding: const EdgeInsets.all(16),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(AppRadius.lg),
          child: Stack(
            children: [
              InteractiveViewer(
                minScale: .7,
                maxScale: 4,
                child: AspectRatio(
                  aspectRatio: 1.75,
                  child: Image.network(url, fit: BoxFit.contain),
                ),
              ),
              Positioned(
                left: 12,
                top: 12,
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: AppColors.ink.withValues(alpha: .75),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    label,
                    style: const TextStyle(fontWeight: FontWeight.w900),
                  ),
                ),
              ),
              Positioned(
                right: 6,
                top: 6,
                child: IconButton.filledTonal(
                  onPressed: () => Navigator.of(dialogContext).pop(),
                  icon: const Icon(Icons.close_rounded),
                ),
              ),
            ],
          ),
        ),
      );
    },
  );
}

class _JobsHero extends StatelessWidget {
  const _JobsHero();

  @override
  Widget build(BuildContext context) {
    return const GlassCard(
      gradient: AppGradients.cardGlow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          StatusBadge(
              label: 'Talento Cardbook',
              icon: Icons.work_outline_rounded,
              color: AppColors.gold),
          SizedBox(height: 16),
          Text('White Card Jobs',
              style: TextStyle(
                  fontSize: 32, height: 1.05, fontWeight: FontWeight.w900)),
          SizedBox(height: 8),
          Text(
              'Candidatos, perfiles laborales y conexiones de contratacion desde Cardbook.',
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

String _relativeDraftTime(DateTime updatedAt) {
  final diff = DateTime.now().difference(updatedAt);
  if (diff.inMinutes < 1) return 'hace unos segundos';
  if (diff.inMinutes < 60) return 'hace ${diff.inMinutes} min';
  if (diff.inHours < 24) return 'hace ${diff.inHours} h';
  return 'hace ${diff.inDays} d';
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
