import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/platform/native_actions.dart';
import 'package:mobile_cardbook/features/jobs/data/jobs_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/section_header.dart';
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
                loading: () => const SizedBox(height: 220, child: AsyncStateView.loading()),
                error: (_, __) => const AsyncStateView.error('No pudimos cargar las White Card Jobs.'),
                data: (data) => _JobsContent(data: data),
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: 4),
    );
  }
}

class _JobsContent extends StatelessWidget {
  const _JobsContent({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final myCard = data['my_card'] is Map<String, dynamic> ? data['my_card'] as Map<String, dynamic> : null;
    final available = (data['available_jobs'] as List<dynamic>? ?? []).whereType<Map<String, dynamic>>().toList();
    final recommended = (data['recommended_for_company'] as List<dynamic>? ?? []).whereType<Map<String, dynamic>>().toList();
    return Column(
      children: [
        if (myCard != null) ...[
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SectionHeader(title: 'Mi White Card', actionLabel: 'Publica'),
                const SizedBox(height: 12),
                _JobTile(job: myCard, highlighted: true),
              ],
            ),
          ),
          const SizedBox(height: 18),
        ],
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionHeader(title: 'Recomendados', actionLabel: 'Afinidad'),
              const SizedBox(height: 12),
              if (recommended.isEmpty)
                const AsyncStateView.empty('Cuando una empresa busque talento, veras recomendaciones aqui.')
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
              const SectionHeader(title: 'Buscan trabajo', actionLabel: 'Explorar'),
              const SizedBox(height: 12),
              if (available.isEmpty)
                const AsyncStateView.empty('No hay White Card Jobs disponibles ahora.')
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
}

class _JobTile extends StatelessWidget {
  const _JobTile({required this.job, this.highlighted = false});

  final Map<String, dynamic> job;
  final bool highlighted;

  @override
  Widget build(BuildContext context) {
    final specialty = job['specialty_detail'] is Map<String, dynamic> ? job['specialty_detail'] as Map<String, dynamic> : {};
    final title = _text(job['title'], fallback: _text(specialty['name'], fallback: 'White Card Job'));
    final name = _text(job['display_name'], fallback: _text(job['username'], fallback: 'Candidato'));
    final description = _text(job['short_description'], fallback: _text(specialty['category'], fallback: 'Disponible para nuevas oportunidades.'));
    final publicUrl = _text(job['public_url']);
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: highlighted ? AppColors.blue.withOpacity(.22) : AppColors.inkAlt.withOpacity(.72),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: highlighted ? AppColors.blue.withOpacity(.42) : AppColors.stroke),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 24,
            backgroundColor: Colors.white,
            backgroundImage: _text(job['photo']).isEmpty ? null : NetworkImage(_text(job['photo'])),
            child: _text(job['photo']).isEmpty ? Text(_initials(name), style: const TextStyle(color: AppColors.ink, fontWeight: FontWeight.w900)) : null,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w900)),
                const SizedBox(height: 3),
                Text(title, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: AppColors.gold, fontWeight: FontWeight.w800)),
                const SizedBox(height: 3),
                Text(description, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(color: AppColors.muted, fontSize: 12)),
              ],
            ),
          ),
          IconButton(
            onPressed: publicUrl.isEmpty ? null : () => NativeActions.shareText(name, publicUrl),
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
          StatusBadge(label: 'Talento Cardbook', icon: Icons.work_outline_rounded, color: AppColors.gold),
          SizedBox(height: 16),
          Text('White Card Jobs', style: TextStyle(fontSize: 32, height: 1.05, fontWeight: FontWeight.w900)),
          SizedBox(height: 8),
          Text('Candidatos, perfiles laborales y conexiones de contratacion desde Cardbook.', style: TextStyle(color: AppColors.muted, height: 1.45)),
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
  final words = value.trim().split(RegExp(r'\s+')).where((word) => word.isNotEmpty).toList();
  if (words.isEmpty) return 'CB';
  if (words.length == 1) return words.first.substring(0, words.first.length >= 2 ? 2 : 1).toUpperCase();
  return '${words[0][0]}${words[1][0]}'.toUpperCase();
}
