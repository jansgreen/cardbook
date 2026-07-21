import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:mobile_cardbook/features/diagnostics/data/diagnostics_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/app_main_menu.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class DiagnosticsScreen extends ConsumerWidget {
  const DiagnosticsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final report = ref.watch(diagnosticsProvider);

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(diagnosticsProvider);
              await ref.read(diagnosticsProvider.future);
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
              children: [
                BrandHeader(
                  trailing: IconButton.filledTonal(
                    onPressed: () => AppMainMenu.show(context),
                    icon: const Icon(Icons.menu_rounded),
                  ),
                ),
                const SizedBox(height: 24),
                const Text(
                  'Diagnostico movil',
                  style: TextStyle(
                    fontSize: 32,
                    height: 1.05,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Valida API, sesion, version publicada y estado operativo de Cardbook.',
                  style: TextStyle(color: AppColors.muted, height: 1.45),
                ),
                const SizedBox(height: 18),
                report.when(
                  loading: () => const SizedBox(
                    height: 260,
                    child: AsyncStateView.loading(),
                  ),
                  error: (_, __) => _DiagnosticsError(
                    onRetry: () => ref.invalidate(diagnosticsProvider),
                  ),
                  data: (data) => _DiagnosticsContent(report: data),
                ),
              ],
            ),
          ),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: 4),
    );
  }
}

class _DiagnosticsContent extends StatelessWidget {
  const _DiagnosticsContent({required this.report});

  final DiagnosticsReport report;

  @override
  Widget build(BuildContext context) {
    final date = DateFormat('dd MMM yyyy, h:mm a').format(report.generatedAt);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        GlassCard(
          gradient: AppGradients.cardGlow,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              StatusBadge(
                label: report.isHealthy
                    ? 'Operativo'
                    : '${report.failCount} alerta critica',
                icon: report.isHealthy
                    ? Icons.verified_rounded
                    : Icons.warning_rounded,
                color: report.isHealthy ? AppColors.green : AppColors.red,
              ),
              const SizedBox(height: 16),
              Text(
                '${report.okCount} OK | ${report.warningCount} avisos | ${report.failCount} fallos',
                style:
                    const TextStyle(fontSize: 22, fontWeight: FontWeight.w900),
              ),
              const SizedBox(height: 8),
              Text(
                'Ultima prueba: $date',
                style: const TextStyle(color: AppColors.muted),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        GlassCard(
          child: Column(
            children: [
              _InfoRow(
                icon: Icons.android_rounded,
                label: 'App instalada',
                value:
                    '${report.appVersionName} (${report.appVersionCode}) | ${report.packageName}',
              ),
              _InfoRow(
                icon: Icons.cloud_rounded,
                label: 'API REST',
                value: report.apiBaseUrl,
              ),
              _InfoRow(
                icon: Icons.public_rounded,
                label: 'Web publica',
                value: report.publicBaseUrl,
              ),
              _InfoRow(
                icon: Icons.key_rounded,
                label: 'Tokens locales',
                value:
                    'Access: ${_yesNo(report.hasAccessToken)} | Refresh: ${_yesNo(report.hasRefreshToken)}',
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        const Text('Pruebas',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
        const SizedBox(height: 10),
        ...report.checks.map(
          (check) => Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: _CheckCard(check: check),
          ),
        ),
      ],
    );
  }
}

class _CheckCard extends StatelessWidget {
  const _CheckCard({required this.check});

  final DiagnosticCheck check;

  @override
  Widget build(BuildContext context) {
    final color = switch (check.state) {
      DiagnosticState.ok => AppColors.green,
      DiagnosticState.warning => AppColors.gold,
      DiagnosticState.fail => AppColors.red,
    };
    final icon = switch (check.state) {
      DiagnosticState.ok => Icons.check_circle_rounded,
      DiagnosticState.warning => Icons.info_rounded,
      DiagnosticState.fail => Icons.error_rounded,
    };

    return GlassCard(
      padding: const EdgeInsets.all(16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: color.withValues(alpha: .14),
              borderRadius: BorderRadius.circular(15),
            ),
            child: Icon(icon, color: color),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        check.title,
                        style: const TextStyle(fontWeight: FontWeight.w900),
                      ),
                    ),
                    if (check.statusCode != null)
                      Text(
                        'HTTP ${check.statusCode}',
                        style: TextStyle(
                          color: color,
                          fontSize: 12,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  check.target,
                  style: const TextStyle(color: AppColors.muted, fontSize: 12),
                ),
                const SizedBox(height: 8),
                Text(check.message, style: const TextStyle(height: 1.35)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: AppColors.purple, size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: const TextStyle(fontWeight: FontWeight.w900)),
                const SizedBox(height: 3),
                Text(
                  value,
                  style: const TextStyle(color: AppColors.muted, height: 1.35),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _DiagnosticsError extends StatelessWidget {
  const _DiagnosticsError({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        children: [
          const AsyncStateView.error(
            'No pudimos ejecutar el diagnostico movil.',
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh_rounded),
            label: const Text('Reintentar'),
          ),
        ],
      ),
    );
  }
}

String _yesNo(bool value) => value ? 'si' : 'no';
