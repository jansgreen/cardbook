import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/home/data/mobile_dashboard_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/app_main_menu.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/company_tile.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/metric_card.dart';
import 'package:mobile_cardbook/shared/widgets/offline_notice.dart';
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
            data: (data) => _DashboardContent(
              data: data,
              onRefresh: () async {
                ref.invalidate(mobileDashboardProvider);
                await ref.read(mobileDashboardProvider.future);
              },
            ),
          ),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: 0),
    );
  }
}

class _DashboardContent extends StatelessWidget {
  const _DashboardContent({required this.data, required this.onRefresh});

  final Map<String, dynamic> data;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    final user = data['user'] as Map<String, dynamic>? ?? {};
    final summary = data['summary'] as Map<String, dynamic>? ?? {};
    final accountType = data['account_type']?.toString() ?? 'company';
    final capabilities = data['capabilities'] is Map<String, dynamic>
        ? data['capabilities'] as Map<String, dynamic>
        : const <String, dynamic>{};
    final companies = (data['companies'] as List<dynamic>? ?? [])
        .whereType<Map<String, dynamic>>()
        .toList();
    final posts = (data['recent_posts'] as List<dynamic>? ?? [])
        .whereType<Map<String, dynamic>>()
        .toList();
    final suggested = (data['suggested_companies'] as List<dynamic>? ?? [])
        .whereType<Map<String, dynamic>>()
        .toList();
    final username = _displayName(user);
    final isOffline = data['_offline'] == true;

    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
        children: [
          BrandHeader(
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                _HeaderIconButton(
                  icon: Icons.notifications_none_rounded,
                  onTap: () => context.go('/notifications'),
                ),
                const SizedBox(width: 8),
                _HeaderIconButton(
                  icon: Icons.menu_rounded,
                  onTap: () => AppMainMenu.show(context),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          _WelcomeHero(accountType: accountType, username: username),
          const SizedBox(height: 18),
          if (isOffline) ...[
            const OfflineNotice(),
            const SizedBox(height: 18),
          ],
          _SummaryPanel(
            accountType: accountType,
            summary: summary,
            capabilities: capabilities,
          ),
          const SizedBox(height: 18),
          _NextStepPanel(
            accountType: accountType,
            summary: summary,
            capabilities: capabilities,
          ),
          const SizedBox(height: 18),
          if (accountType == 'job')
            _JobDashboardSections(suggested: suggested, summary: summary)
          else if (accountType == 'agent')
            _AgentDashboardSections(
              companies: companies,
              posts: posts,
              suggested: suggested,
            )
          else
            _CompanyDashboardSections(
              companies: companies,
              posts: posts,
              suggested: suggested,
              isAdmin: accountType == 'superuser',
            ),
        ],
      ),
    );
  }
}

class _SummaryPanel extends StatelessWidget {
  const _SummaryPanel({
    required this.accountType,
    required this.summary,
    required this.capabilities,
  });

  final String accountType;
  final Map<String, dynamic> summary;
  final Map<String, dynamic> capabilities;

  @override
  Widget build(BuildContext context) {
    final metrics = _metricsFor(accountType, summary, capabilities);
    return GlassCard(
      gradient: AppGradients.cardGlow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(title: 'Resumen rapido'),
          const SizedBox(height: 12),
          GridView.count(
            crossAxisCount: 3,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 10,
            mainAxisSpacing: 10,
            childAspectRatio: .9,
            children: [
              for (final metric in metrics)
                MetricCard(
                  label: metric.label,
                  value: metric.value,
                  icon: metric.icon,
                  accent: metric.color,
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _NextStepPanel extends StatelessWidget {
  const _NextStepPanel({
    required this.accountType,
    required this.summary,
    required this.capabilities,
  });

  final String accountType;
  final Map<String, dynamic> summary;
  final Map<String, dynamic> capabilities;

  @override
  Widget build(BuildContext context) {
    final step = _nextStepFor(accountType, summary, capabilities);
    return GlassCard(
      borderColor: step.color.withValues(alpha: .32),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: step.color.withValues(alpha: .16),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Icon(step.icon, color: step.color),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(step.title,
                    style: const TextStyle(
                        fontSize: 16, fontWeight: FontWeight.w900)),
                const SizedBox(height: 4),
                Text(step.description,
                    style:
                        const TextStyle(color: AppColors.muted, height: 1.35)),
              ],
            ),
          ),
          const SizedBox(width: 10),
          FilledButton(
            onPressed: () => context.go(step.path),
            style: FilledButton.styleFrom(
              minimumSize: const Size(0, 44),
              padding: const EdgeInsets.symmetric(horizontal: 14),
            ),
            child: Text(step.actionLabel),
          ),
        ],
      ),
    );
  }
}

class _CompanyDashboardSections extends StatelessWidget {
  const _CompanyDashboardSections({
    required this.companies,
    required this.posts,
    required this.suggested,
    required this.isAdmin,
  });

  final List<Map<String, dynamic>> companies;
  final List<Map<String, dynamic>> posts;
  final List<Map<String, dynamic>> suggested;
  final bool isAdmin;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _ActionGrid(
          actions: [
            _QuickAction('Nueva empresa', Icons.add_business_rounded,
                AppColors.blue, '/companies/form'),
            _QuickAction(
                'Tarjetas', Icons.badge_rounded, AppColors.purple, '/cards'),
            _QuickAction(
                'Website', Icons.public_rounded, AppColors.cyan, '/websites'),
            _QuickAction(
                'Book', Icons.bookmarks_rounded, AppColors.gold, '/book'),
            if (isAdmin)
              _QuickAction('Diagnostico', Icons.health_and_safety_rounded,
                  AppColors.green, '/diagnostics'),
          ],
        ),
        const SizedBox(height: 18),
        _CompaniesPanel(companies: companies),
        const SizedBox(height: 18),
        _PostsPanel(posts: posts),
        const SizedBox(height: 18),
        _SuggestedPanel(suggested: suggested),
      ],
    );
  }
}

class _JobDashboardSections extends StatelessWidget {
  const _JobDashboardSections({
    required this.suggested,
    required this.summary,
  });

  final List<Map<String, dynamic>> suggested;
  final Map<String, dynamic> summary;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _ActionGrid(
          actions: const [
            _QuickAction('Crear White Card', Icons.work_rounded,
                AppColors.purple, '/jobs/form'),
            _QuickAction('Buscar empresas', Icons.travel_explore_rounded,
                AppColors.blue, '/companies'),
            _QuickAction(
                'Abrir Book', Icons.bookmarks_rounded, AppColors.gold, '/book'),
            _QuickAction('Notificaciones', Icons.notifications_rounded,
                AppColors.cyan, '/notifications'),
          ],
        ),
        const SizedBox(height: 18),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionHeader(title: 'Tu ruta laboral'),
              const SizedBox(height: 12),
              _InfoStep(
                icon: Icons.badge_rounded,
                title: 'Crea tu White Card Job',
                text: 'Presenta tu perfil laboral con QR y enlace publico.',
              ),
              _InfoStep(
                icon: Icons.bookmark_add_rounded,
                title: 'Guarda oportunidades en Book',
                text: 'Conserva empresas y tarjetas que compartan contigo.',
              ),
              _InfoStep(
                icon: Icons.share_rounded,
                title: 'Comparte tu perfil',
                text: 'Usa QR, enlace, WhatsApp o herramientas nativas.',
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        _SuggestedPanel(
          suggested: suggested,
          title: 'Empresas recomendadas',
          empty: 'Cuando haya empresas disponibles, apareceran aqui.',
        ),
      ],
    );
  }
}

class _AgentDashboardSections extends StatelessWidget {
  const _AgentDashboardSections({
    required this.companies,
    required this.posts,
    required this.suggested,
  });

  final List<Map<String, dynamic>> companies;
  final List<Map<String, dynamic>> posts;
  final List<Map<String, dynamic>> suggested;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _ActionGrid(
          actions: const [
            _QuickAction('Alianzas', Icons.handshake_rounded, AppColors.purple,
                '/alliances'),
            _QuickAction('Nueva empresa', Icons.add_business_rounded,
                AppColors.blue, '/companies/form'),
            _QuickAction(
                'Tarjetas', Icons.badge_rounded, AppColors.gold, '/cards'),
            _QuickAction(
                'White Card', Icons.work_rounded, AppColors.green, '/jobs'),
          ],
        ),
        const SizedBox(height: 18),
        GlassCard(
          gradient: AppGradients.cardGlow,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const [
              StatusBadge(
                label: 'Agente Cardbook',
                icon: Icons.verified_rounded,
                color: AppColors.gold,
              ),
              SizedBox(height: 14),
              Text('Tu panel comercial',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
              SizedBox(height: 6),
              Text(
                'Crea empresas, tarjetas y conexiones para clientes. Finanzas y accesos quedan reservados al superusuario.',
                style: TextStyle(color: AppColors.muted, height: 1.45),
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        _CompaniesPanel(companies: companies, title: 'Empresas gestionadas'),
        const SizedBox(height: 18),
        _PostsPanel(posts: posts),
        const SizedBox(height: 18),
        _SuggestedPanel(suggested: suggested),
      ],
    );
  }
}

class _ActionGrid extends StatelessWidget {
  const _ActionGrid({required this.actions});

  final List<_QuickAction> actions;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(title: 'Accesos rapidos'),
          const SizedBox(height: 12),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 10,
            mainAxisSpacing: 10,
            childAspectRatio: 1.65,
            children: [
              for (final action in actions)
                InkWell(
                  onTap: () => context.go(action.path),
                  borderRadius: BorderRadius.circular(AppRadius.md),
                  child: Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: action.color.withValues(alpha: .12),
                      borderRadius: BorderRadius.circular(AppRadius.md),
                      border: Border.all(
                          color: action.color.withValues(alpha: .28)),
                    ),
                    child: Row(
                      children: [
                        Icon(action.icon, color: action.color),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(action.label,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style:
                                  const TextStyle(fontWeight: FontWeight.w900)),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _CompaniesPanel extends StatelessWidget {
  const _CompaniesPanel({
    required this.companies,
    this.title = 'Empresas activas',
  });

  final List<Map<String, dynamic>> companies;
  final String title;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: title,
            actionLabel: 'Ver todas',
            onAction: () => context.go('/companies'),
          ),
          const SizedBox(height: 12),
          if (companies.isEmpty)
            const _EmptyState(message: 'Aun no hay empresas activas.')
          else
            for (final company in companies) ...[
              CompanyTile(
                name: company['name']?.toString() ?? 'Empresa',
                description:
                    company['description']?.toString() ?? 'Empresa Cardbook',
                rating: _compactNumber(company['efficient_count']),
                logoUrl: company['logo']?.toString(),
                onTap: () => context.push('/companies/detail', extra: company),
              ),
              const SizedBox(height: 10),
            ],
        ],
      ),
    );
  }
}

class _PostsPanel extends StatelessWidget {
  const _PostsPanel({required this.posts});

  final List<Map<String, dynamic>> posts;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(title: 'Publicaciones recientes'),
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
    );
  }
}

class _SuggestedPanel extends StatelessWidget {
  const _SuggestedPanel({
    required this.suggested,
    this.title = 'Empresas sugeridas',
    this.empty = 'Cuando haya afinidad, veras sugerencias aqui.',
  });

  final List<Map<String, dynamic>> suggested;
  final String title;
  final String empty;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: title,
            actionLabel: 'Explorar',
            onAction: () => context.go('/companies'),
          ),
          const SizedBox(height: 12),
          if (suggested.isEmpty)
            _EmptyState(message: empty)
          else
            for (final company in suggested.take(3)) ...[
              CompanyTile(
                name: company['name']?.toString() ?? 'Empresa',
                description:
                    company['category']?.toString() ?? 'Empresa sugerida',
                rating: _compactNumber(company['efficient_count']),
                logoUrl: company['logo']?.toString(),
                onTap: () => context.push('/companies/detail', extra: company),
              ),
              const SizedBox(height: 10),
            ],
        ],
      ),
    );
  }
}

class _WelcomeHero extends StatelessWidget {
  const _WelcomeHero({required this.accountType, required this.username});

  final String accountType;
  final String username;

  @override
  Widget build(BuildContext context) {
    final profile = _profileFor(accountType);
    return GlassCard(
      padding: const EdgeInsets.all(18),
      gradient: const LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [Color(0x993B36FF), Color(0x661E63FF), Color(0x2200D7FF)],
      ),
      borderColor: profile.color.withValues(alpha: .32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          StatusBadge(
            label: profile.badge,
            icon: profile.icon,
            color: profile.color,
          ),
          const SizedBox(height: 18),
          Text(
            'Hola, $username',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 6),
          Text(
            profile.message,
            style: const TextStyle(color: AppColors.muted, height: 1.45),
          ),
        ],
      ),
    );
  }
}

class _InfoStep extends StatelessWidget {
  const _InfoStep({
    required this.icon,
    required this.title,
    required this.text,
  });

  final IconData icon;
  final String title;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: AppColors.purple, size: 22),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: const TextStyle(fontWeight: FontWeight.w900)),
                const SizedBox(height: 2),
                Text(text,
                    style:
                        const TextStyle(color: AppColors.muted, height: 1.35)),
              ],
            ),
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
          color: AppColors.panelSoft.withValues(alpha: .72),
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
        color: AppColors.inkAlt.withValues(alpha: .7),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.stroke),
      ),
      child: Text(message, style: const TextStyle(color: AppColors.muted)),
    );
  }
}

class _MetricSpec {
  const _MetricSpec(this.label, this.value, this.icon, this.color);

  final String label;
  final String value;
  final IconData icon;
  final Color color;
}

class _QuickAction {
  const _QuickAction(this.label, this.icon, this.color, this.path);

  final String label;
  final IconData icon;
  final Color color;
  final String path;
}

class _NextStep {
  const _NextStep({
    required this.title,
    required this.description,
    required this.actionLabel,
    required this.path,
    required this.icon,
    required this.color,
  });

  final String title;
  final String description;
  final String actionLabel;
  final String path;
  final IconData icon;
  final Color color;
}

class _ProfileCopy {
  const _ProfileCopy({
    required this.badge,
    required this.message,
    required this.icon,
    required this.color,
  });

  final String badge;
  final String message;
  final IconData icon;
  final Color color;
}

List<_MetricSpec> _metricsFor(
  String accountType,
  Map<String, dynamic> summary,
  Map<String, dynamic> capabilities,
) {
  if (accountType == 'job') {
    return [
      _MetricSpec('Book', '${summary['book_items'] ?? 0}',
          Icons.bookmark_rounded, AppColors.gold),
      _MetricSpec('Empresas', '${summary['companies'] ?? 0}',
          Icons.business_rounded, AppColors.blue),
      _MetricSpec('Avisos', '${summary['notifications'] ?? 0}',
          Icons.notifications_rounded, AppColors.cyan),
      _MetricSpec(
          'White Card',
          capabilities['can_create_white_card_job'] == true ? 'Lista' : 'Pend.',
          Icons.work_rounded,
          AppColors.purple),
      _MetricSpec('Alianzas', '${summary['alliances'] ?? 0}',
          Icons.handshake_rounded, AppColors.green),
      _MetricSpec('Vistas', _compactNumber(summary['views']),
          Icons.visibility_rounded, AppColors.violet),
    ];
  }
  if (accountType == 'agent') {
    return [
      _MetricSpec('Empresas', '${summary['companies'] ?? 0}',
          Icons.business_rounded, AppColors.blue),
      _MetricSpec('Tarjetas', '${summary['business_cards'] ?? 0}',
          Icons.badge_rounded, AppColors.gold),
      _MetricSpec('Alianzas', '${summary['alliances'] ?? 0}',
          Icons.handshake_rounded, AppColors.green),
      _MetricSpec('Pendientes', '${summary['pending_alliances'] ?? 0}',
          Icons.schedule_rounded, AppColors.cyan),
      _MetricSpec('Posts', '${summary['posts'] ?? 0}', Icons.article_rounded,
          AppColors.purple),
      _MetricSpec('Book', '${summary['book_items'] ?? 0}',
          Icons.bookmark_rounded, AppColors.violet),
    ];
  }
  return [
    _MetricSpec('Empresas', '${summary['companies'] ?? 0}',
        Icons.business_rounded, AppColors.blue),
    _MetricSpec('Posts', '${summary['posts'] ?? 0}', Icons.article_rounded,
        AppColors.purple),
    _MetricSpec('Excelentes', _compactNumber(summary['excellent']),
        Icons.star_rounded, AppColors.gold),
    _MetricSpec('Vistas', _compactNumber(summary['views']),
        Icons.visibility_rounded, AppColors.cyan),
    _MetricSpec('Alianzas', '${summary['alliances'] ?? 0}',
        Icons.handshake_rounded, AppColors.green),
    _MetricSpec('Book', '${summary['book_items'] ?? 0}', Icons.bookmark_rounded,
        AppColors.violet),
  ];
}

_NextStep _nextStepFor(
  String accountType,
  Map<String, dynamic> summary,
  Map<String, dynamic> capabilities,
) {
  if (accountType == 'job') {
    return const _NextStep(
      title: 'Prepara tu White Card Job',
      description:
          'Crea o actualiza tu tarjeta laboral para compartirla con QR.',
      actionLabel: 'Abrir',
      path: '/jobs',
      icon: Icons.work_rounded,
      color: AppColors.purple,
    );
  }
  if (accountType == 'agent') {
    return const _NextStep(
      title: 'Gestiona tu red de clientes',
      description: 'Crea empresas, tarjetas y alianzas desde tu panel movil.',
      actionLabel: 'Alianzas',
      path: '/alliances',
      icon: Icons.handshake_rounded,
      color: AppColors.gold,
    );
  }
  final companyCount =
      summary['companies'] is num ? summary['companies'] as num : 0;
  if (companyCount == 0 && capabilities['can_create_company'] == true) {
    return const _NextStep(
      title: 'Crea tu primera empresa',
      description: 'Luego podras agregar perfiles, tarjetas y website.',
      actionLabel: 'Crear',
      path: '/companies/form',
      icon: Icons.add_business_rounded,
      color: AppColors.blue,
    );
  }
  return const _NextStep(
    title: 'Comparte tu presencia digital',
    description: 'Administra tarjetas, Book y conexiones desde Cardbook.',
    actionLabel: 'Tarjetas',
    path: '/cards',
    icon: Icons.qr_code_2_rounded,
    color: AppColors.purple,
  );
}

_ProfileCopy _profileFor(String accountType) {
  if (accountType == 'job') {
    return const _ProfileCopy(
      badge: 'Buscando trabajo',
      message: 'Gestiona tu White Card Job y guarda oportunidades en Book.',
      icon: Icons.work_rounded,
      color: AppColors.gold,
    );
  }
  if (accountType == 'agent') {
    return const _ProfileCopy(
      badge: 'Agente Cardbook',
      message: 'Construye relaciones, tarjetas y empresas para tus clientes.',
      icon: Icons.handshake_rounded,
      color: AppColors.green,
    );
  }
  if (accountType == 'superuser') {
    return const _ProfileCopy(
      badge: 'Superusuario',
      message: 'Supervisa la plataforma y valida la experiencia completa.',
      icon: Icons.admin_panel_settings_rounded,
      color: AppColors.cyan,
    );
  }
  return const _ProfileCopy(
    badge: 'Empresa Cardbook',
    message: 'Conecta, comparte y crece desde tu red empresarial.',
    icon: Icons.verified_rounded,
    color: AppColors.gold,
  );
}

String _displayName(Map<String, dynamic> user) {
  final firstName = (user['first_name'] as String?)?.trim();
  if (firstName?.isNotEmpty == true) return firstName!;
  final username = (user['username'] as String?)?.trim();
  return username?.isNotEmpty == true ? username! : 'Cardbook';
}

String _compactNumber(dynamic value) {
  final number =
      value is num ? value : num.tryParse(value?.toString() ?? '') ?? 0;
  if (number >= 1000000) return '${(number / 1000000).toStringAsFixed(1)}m';
  if (number >= 1000) return '${(number / 1000).toStringAsFixed(1)}k';
  return number.toInt().toString();
}

class _DashboardLoading extends StatelessWidget {
  const _DashboardLoading();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: SizedBox(
        width: 36,
        height: 36,
        child:
            CircularProgressIndicator(strokeWidth: 3, color: AppColors.purple),
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
        child: Text('No pudimos cargar el dashboard movil.',
            textAlign: TextAlign.center),
      ),
    );
  }
}
