import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/features/notifications/data/notifications_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/section_header.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final alliances = ref.watch(alliancesProvider);

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
            children: [
              const BrandHeader(),
              const SizedBox(height: 24),
              const _NotificationsHero(),
              const SizedBox(height: 18),
              GlassCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SectionHeader(title: 'Alianzas', actionLabel: 'Ver todas'),
                    const SizedBox(height: 12),
                    alliances.when(
                      loading: () => const SizedBox(height: 120, child: AsyncStateView.loading()),
                      error: (_, __) => const AsyncStateView.error('No pudimos cargar tus notificaciones.'),
                      data: (items) => items.isEmpty
                          ? const AsyncStateView.empty('No tienes solicitudes ni alianzas recientes.')
                          : Column(
                              children: [
                                for (final item in items) ...[
                                  _AllianceTile(item: item),
                                  const SizedBox(height: 10),
                                ],
                              ],
                            ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: 3),
    );
  }
}

class _AllianceTile extends ConsumerWidget {
  const _AllianceTile({required this.item});

  final Map<String, dynamic> item;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final requester = item['requester_detail'] is Map<String, dynamic> ? item['requester_detail'] as Map<String, dynamic> : <String, dynamic>{};
    final receiver = item['receiver_detail'] is Map<String, dynamic> ? item['receiver_detail'] as Map<String, dynamic> : <String, dynamic>{};
    final status = item['status']?.toString() ?? 'pending';
    final requesterName = requester['name']?.toString() ?? 'Empresa';
    final receiverName = receiver['name']?.toString() ?? 'Empresa';

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.inkAlt.withOpacity(.72),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.stroke),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: _statusColor(status).withOpacity(.14),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(Icons.handshake_rounded, color: _statusColor(status)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('$requesterName + $receiverName', maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w900)),
                    const SizedBox(height: 4),
                    Text(_statusLabel(status), style: const TextStyle(color: AppColors.muted, fontSize: 12)),
                  ],
                ),
              ),
              StatusBadge(label: _statusLabel(status), color: _statusColor(status)),
            ],
          ),
          if (status == 'pending') ...[
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _decide(context, ref, 'rejected'),
                    icon: const Icon(Icons.close_rounded),
                    label: const Text('Rechazar'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: () => _decide(context, ref, 'accepted'),
                    icon: const Icon(Icons.check_rounded),
                    label: const Text('Aceptar'),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _decide(BuildContext context, WidgetRef ref, String decision) async {
    final id = item['id'];
    if (id is! int) return;
    try {
      await ref.read(allianceRepositoryProvider).decide(allianceId: id, decision: decision);
      ref.invalidate(alliancesProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(decision == 'accepted' ? 'Alianza aceptada.' : 'Alianza rechazada.')),
        );
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No pudimos actualizar la alianza.')),
        );
      }
    }
  }

  Color _statusColor(String status) {
    if (status == 'accepted') return AppColors.green;
    if (status == 'rejected') return AppColors.red;
    return AppColors.gold;
  }

  String _statusLabel(String status) {
    if (status == 'accepted') return 'Aceptada';
    if (status == 'rejected') return 'Rechazada';
    return 'Pendiente';
  }
}

class _NotificationsHero extends StatelessWidget {
  const _NotificationsHero();

  @override
  Widget build(BuildContext context) {
    return const GlassCard(
      gradient: AppGradients.cardGlow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          StatusBadge(label: 'Actividad', icon: Icons.notifications_active_rounded, color: AppColors.gold),
          SizedBox(height: 16),
          Text('Notificaciones', style: TextStyle(fontSize: 32, height: 1.05, fontWeight: FontWeight.w900)),
          SizedBox(height: 8),
          Text(
            'Solicitudes, alianzas y eventos importantes para tu red Cardbook.',
            style: TextStyle(color: AppColors.muted, height: 1.45),
          ),
        ],
      ),
    );
  }
}
