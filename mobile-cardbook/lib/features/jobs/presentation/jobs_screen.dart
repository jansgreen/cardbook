import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
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

class JobsScreen extends ConsumerWidget {
  const JobsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final jobs = ref.watch(mobileJobsProvider);
    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
            children: [
              const BrandHeader(),
              const SizedBox(height: 24),
              const _JobsHero(),
              const SizedBox(height: 18),
              jobs.when(
                loading: () => const SizedBox(
                    height: 220, child: AsyncStateView.loading()),
                error: (_, __) => AsyncStateView.error(
                  'No pudimos cargar las White Card Jobs.',
                  actionLabel: 'Reintentar',
                  onAction: () => ref.invalidate(mobileJobsProvider),
                ),
                data: (data) => _JobsContent(data: data),
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: null),
    );
  }
}

class _JobsContent extends ConsumerWidget {
  const _JobsContent({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final myCard = data['my_card'] is Map<String, dynamic>
        ? data['my_card'] as Map<String, dynamic>
        : null;
    final available = (data['available_jobs'] as List<dynamic>? ?? [])
        .whereType<Map<String, dynamic>>()
        .toList();
    final recommended =
        (data['recommended_for_company'] as List<dynamic>? ?? [])
            .whereType<Map<String, dynamic>>()
            .toList();
    final isOffline = data['_offline'] == true;
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
                const SectionHeader(
                    title: 'Mi White Card', actionLabel: 'Publica'),
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
            icon: const Icon(Icons.ios_share_rounded, color: AppColors.text),
          ),
        ],
      ),
    );
  }
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
