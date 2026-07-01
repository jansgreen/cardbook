import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/home/data/mobile_dashboard_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/company_tile.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/metric_card.dart';
import 'package:mobile_cardbook/shared/widgets/post_preview_card.dart';
import 'package:mobile_cardbook/shared/widgets/section_header.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(mobileDashboardProvider);
    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: dashboard.when(
            loading: () => const _DashboardLoading(),
            error: (_, __) => const _DashboardError(),
            data: (data) => _DashboardContent(data: data),
          ),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: 0),
    );
  }
}

class _DashboardContent extends StatelessWidget {
  const _DashboardContent({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final user = data['user'] as Map<String, dynamic>? ?? {};
    final summary = data['summary'] as Map<String, dynamic>? ?? {};
    final companies = (data['companies'] as List<dynamic>? ?? []).cast<Map<String, dynamic>>();
    final posts = (data['recent_posts'] as List<dynamic>? ?? []).cast<Map<String, dynamic>>();
    final suggested = (data['suggested_companies'] as List<dynamic>? ?? []).cast<Map<String, dynamic>>();
    final firstName = (user['first_name'] as String?)?.trim();
    final username = firstName?.isNotEmpty == true ? firstName! : (user['username'] as String? ?? 'Cardbook');
    final totalViews = _compactNumber(summary['views']);
    final excellent = _compactNumber(summary['excellent']);

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
      children: [
        BrandHeader(
          trailing: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              _HeaderIconButton(icon: Icons.notifications_none_rounded, onTap: () {}),
              const SizedBox(width: 8),
              _HeaderIconButton(icon: Icons.menu_rounded, onTap: () {}),
            ],
          ),
        ),
        const SizedBox(height: 24),
        _WelcomeHero(username: username),
        const SizedBox(height: 18),
        GlassCard(
          gradient: AppGradients.cardGlow,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionHeader(title: 'Resumen rapido', actionLabel: 'Ver todo'),
              const SizedBox(height: 12),
              GridView.count(
                crossAxisCount: 3,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisSpacing: 10,
                mainAxisSpacing: 10,
                childAspectRatio: .9,
                children: [
                  MetricCard(label: 'Empresas', value: '${summary['companies'] ?? 0}', icon: Icons.business_rounded),
                  MetricCard(label: 'Publicaciones', value: '${summary['posts'] ?? 0}', icon: Icons.article_rounded, accent: AppColors.blue),
                  MetricCard(label: 'Excelentes', value: excellent, icon: Icons.star_rounded, accent: AppColors.gold),
                  MetricCard(label: 'Vistas', value: totalViews, icon: Icons.visibility_rounded, accent: AppColors.cyan),
                  MetricCard(label: 'Alianzas', value: '${summary['alliances'] ?? 0}', icon: Icons.handshake_rounded, accent: AppColors.green),
                  MetricCard(label: 'Book', value: '${summary['book_items'] ?? 0}', icon: Icons.bookmark_rounded, accent: AppColors.violet),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionHeader(title: 'Empresas activas', actionLabel: 'Ver todas'),
              const SizedBox(height: 12),
              if (companies.isEmpty)
                const _EmptyState(message: 'Aun no tienes empresas activas.')
              else
                for (final company in companies) ...[
                  CompanyTile(
                    name: company['name']?.toString() ?? 'Empresa',
                    description: company['description']?.toString() ?? 'Empresa en Cardbook',
                    rating: _compactNumber(company['efficient_count']),
                    logoUrl: company['logo']?.toString(),
                    onTap: () => context.push('/companies/detail', extra: company),
                  ),
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
              const SectionHeader(title: 'Publicaciones recientes', actionLabel: 'Ver todas'),
              const SizedBox(height: 12),
              if (posts.isEmpty)
                const _EmptyState(message: 'No hay publicaciones recientes.')
              else
                for (final post in posts.take(2)) ...[
                  PostPreviewCard(
                    companyName: post['company_name']?.toString() ?? 'Cardbook',
                    title: post['title']?.toString() ?? 'Publicacion',
                    caption: post['caption']?.toString() ?? '',
                    imageUrl: post['media']?.toString(),
                  ),
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
              const SectionHeader(title: 'Empresas sugeridas', actionLabel: 'Explorar'),
              const SizedBox(height: 12),
              if (suggested.isEmpty)
                const _EmptyState(message: 'Cuando haya afinidad, veras sugerencias aqui.')
              else
                for (final company in suggested.take(3)) ...[
                  CompanyTile(
                    name: company['name']?.toString() ?? 'Empresa',
                    description: company['category']?.toString() ?? 'Empresa sugerida',
                    rating: _compactNumber(company['efficient_count']),
                    logoUrl: company['logo']?.toString(),
                    onTap: () => context.push('/companies/detail', extra: company),
                  ),
                  const SizedBox(height: 10),
                ],
            ],
          ),
        ),
      ],
    );
  }

  static String _compactNumber(dynamic value) {
    final number = value is num ? value : num.tryParse(value?.toString() ?? '') ?? 0;
    if (number >= 1000000) return '${(number / 1000000).toStringAsFixed(1)}m';
    if (number >= 1000) return '${(number / 1000).toStringAsFixed(1)}k';
    return number.toInt().toString();
  }
}

class _WelcomeHero extends StatelessWidget {
  const _WelcomeHero({required this.username});

  final String username;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(18),
      gradient: const LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [Color(0x993B36FF), Color(0x661E63FF), Color(0x2200D7FF)],
      ),
      borderColor: AppColors.blue.withOpacity(.32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const StatusBadge(label: 'Cardbook movil', icon: Icons.verified_rounded, color: AppColors.gold),
          const SizedBox(height: 18),
          Text(
            'Hola, $username',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 6),
          const Text(
            'Conecta, comparte y crece desde tu red empresarial.',
            style: TextStyle(color: AppColors.muted, height: 1.45),
          ),
        ],
      ),
    );
  }
}

class _HeaderIconButton extends StatelessWidget {
  const _HeaderIconButton({required this.icon, required this.onTap});

  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        width: 42,
        height: 42,
        decoration: BoxDecoration(
          color: AppColors.panelSoft.withOpacity(.72),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.stroke),
        ),
        child: Icon(icon, color: AppColors.text, size: 22),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.inkAlt.withOpacity(.7),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.stroke),
      ),
      child: Text(message, style: const TextStyle(color: AppColors.muted)),
    );
  }
}

class _DashboardLoading extends StatelessWidget {
  const _DashboardLoading();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: SizedBox(
        width: 36,
        height: 36,
        child: CircularProgressIndicator(strokeWidth: 3, color: AppColors.purple),
      ),
    );
  }
}

class _DashboardError extends StatelessWidget {
  const _DashboardError();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(24),
        child: Text('No pudimos cargar el dashboard movil.', textAlign: TextAlign.center),
      ),
    );
  }
}
