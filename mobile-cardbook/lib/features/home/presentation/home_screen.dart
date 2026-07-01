import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/features/home/data/mobile_dashboard_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/metric_card.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(mobileDashboardProvider);
    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: dashboard.when(
            loading: () => const Center(child: CircularProgressIndicator()),
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
    final firstName = (user['first_name'] as String?)?.trim();
    final username = firstName?.isNotEmpty == true ? firstName! : (user['username'] as String? ?? 'Cardbook');

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 110),
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text('cardbook', style: TextStyle(fontSize: 26, fontWeight: FontWeight.w900)),
            IconButton(onPressed: () {}, icon: const Icon(Icons.menu)),
          ],
        ),
        const SizedBox(height: 24),
        Text('Hola, $username', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
        const Text('Bienvenido a Cardbook', style: TextStyle(color: AppColors.muted)),
        const SizedBox(height: 22),
        Card(
          color: AppColors.panel.withOpacity(.72),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Resumen rapido', style: TextStyle(fontWeight: FontWeight.w900)),
                    Text('Ver todo', style: TextStyle(color: AppColors.purple, fontSize: 12)),
                  ],
                ),
                const SizedBox(height: 14),
                GridView.count(
                  crossAxisCount: 3,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisSpacing: 10,
                  mainAxisSpacing: 10,
                  childAspectRatio: .92,
                  children: [
                    MetricCard(label: 'Empresas', value: '${summary['companies'] ?? 0}', icon: Icons.business),
                    MetricCard(label: 'Publicaciones', value: '${summary['posts'] ?? 0}', icon: Icons.article_outlined, accent: AppColors.blue),
                    MetricCard(label: 'Excelentes', value: '${summary['excellent'] ?? 0}', icon: Icons.star, accent: AppColors.gold),
                    MetricCard(label: 'Vistas', value: '${summary['views'] ?? 0}', icon: Icons.visibility_outlined, accent: AppColors.cyan),
                    MetricCard(label: 'Alianzas', value: '${summary['alliances'] ?? 0}', icon: Icons.handshake_outlined, accent: AppColors.green),
                    MetricCard(label: 'Book', value: '${summary['book_items'] ?? 0}', icon: Icons.bookmark_border, accent: AppColors.purple),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 18),
        _SectionCard(
          title: 'Empresas activas',
          child: companies.isEmpty
              ? const Text('No hay empresas todavia.', style: TextStyle(color: AppColors.muted))
              : Column(
                  children: [
                    for (final company in companies)
                      _CompanyRow(
                        name: company['name']?.toString() ?? 'Empresa',
                        description: company['description']?.toString() ?? 'Empresa en Cardbook',
                        rating: company['efficient_count']?.toString() ?? '0',
                      ),
                  ],
                ),
        ),
        const SizedBox(height: 18),
        _SectionCard(
          title: 'Publicaciones recientes',
          child: posts.isEmpty
              ? const Text('No hay publicaciones recientes.', style: TextStyle(color: AppColors.muted))
              : Column(
                  children: [
                    for (final post in posts)
                      ListTile(
                        contentPadding: EdgeInsets.zero,
                        title: Text(post['title']?.toString() ?? 'Publicacion'),
                        subtitle: Text(post['caption']?.toString() ?? '', maxLines: 2, overflow: TextOverflow.ellipsis),
                      ),
                  ],
                ),
        ),
      ],
    );
  }
}

class _SectionCard extends StatelessWidget {
  const _SectionCard({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16)),
            const SizedBox(height: 12),
            child,
          ],
        ),
      ),
    );
  }
}

class _CompanyRow extends StatelessWidget {
  const _CompanyRow({required this.name, required this.description, required this.rating});

  final String name;
  final String description;
  final String rating;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: CircleAvatar(
        backgroundColor: AppColors.panelSoft,
        child: Text(_initials(name)),
      ),
      title: Text(name, maxLines: 1, overflow: TextOverflow.ellipsis),
      subtitle: Text(description, maxLines: 1, overflow: TextOverflow.ellipsis),
      trailing: Text('★ $rating', style: const TextStyle(color: AppColors.gold, fontWeight: FontWeight.w800)),
    );
  }

  String _initials(String value) {
    final compact = value.trim();
    if (compact.isEmpty) return 'CB';
    return compact.substring(0, compact.length >= 2 ? 2 : 1).toUpperCase();
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
