import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:mobile_cardbook/features/notifications/data/notifications_repository.dart';
import 'package:mobile_cardbook/features/push/data/push_notification_service.dart';
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
    final notifications = ref.watch(referralNotificationsProvider);
    final alliances = ref.watch(alliancesProvider);

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(referralNotificationsProvider);
              ref.invalidate(alliancesProvider);
              await Future.wait([
                ref.read(referralNotificationsProvider.future),
                ref.read(alliancesProvider.future),
              ]);
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
              children: [
                const BrandHeader(),
                const SizedBox(height: 24),
                notifications.when(
                  loading: () => const _NotificationsHero(unreadCount: 0),
                  error: (_, __) => const _NotificationsHero(unreadCount: 0),
                  data: (data) => _NotificationsHero(
                      unreadCount: _intValue(data['unread_count']) ?? 0),
                ),
                const SizedBox(height: 18),
                _PushPanel(ref: ref),
                const SizedBox(height: 18),
                GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      notifications.when(
                        loading: () => const SectionHeader(
                            title: 'Inbox', actionLabel: 'Cargando'),
                        error: (_, __) => const SectionHeader(
                            title: 'Inbox', actionLabel: 'Error'),
                        data: (data) => SectionHeader(
                          title: 'Inbox',
                          actionLabel:
                              (_intValue(data['unread_count']) ?? 0) > 0
                                  ? 'Marcar leidas'
                                  : 'Al dia',
                          onAction: (_intValue(data['unread_count']) ?? 0) > 0
                              ? () => _markAllRead(context, ref)
                              : null,
                        ),
                      ),
                      const SizedBox(height: 12),
                      notifications.when(
                        loading: () => const SizedBox(
                            height: 140, child: AsyncStateView.loading()),
                        error: (_, __) => AsyncStateView.error(
                          'No pudimos cargar tus notificaciones.',
                          actionLabel: 'Reintentar',
                          onAction: () =>
                              ref.invalidate(referralNotificationsProvider),
                        ),
                        data: (data) {
                          final items = _list(data['results']);
                          if (items.isEmpty) {
                            return const AsyncStateView.empty(
                              'Te avisaremos aqui cuando haya alianzas, pagos, tickets o actividad importante.',
                              title: 'Todo esta al dia',
                              icon: Icons.notifications_none_rounded,
                            );
                          }
                          return Column(
                            children: [
                              for (final item in items) ...[
                                _NotificationTile(item: item),
                                const SizedBox(height: 10),
                              ],
                            ],
                          );
                        },
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      SectionHeader(
                        title: 'Alianzas',
                        actionLabel: 'Gestionar',
                        onAction: () => context.push('/alliances'),
                      ),
                      const SizedBox(height: 12),
                      alliances.when(
                        loading: () => const SizedBox(
                            height: 120, child: AsyncStateView.loading()),
                        error: (_, __) => AsyncStateView.error(
                          'No pudimos cargar el resumen de alianzas.',
                          actionLabel: 'Reintentar',
                          onAction: () => ref.invalidate(alliancesProvider),
                        ),
                        data: (items) => _AllianceSummary(items: items),
                      ),
                    ],
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

  Future<void> _markAllRead(BuildContext context, WidgetRef ref) async {
    try {
      await ref.read(notificationRepositoryProvider).markAllRead();
      ref.invalidate(referralNotificationsProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Notificaciones marcadas como leidas.')),
        );
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text('No pudimos actualizar las notificaciones.')),
        );
      }
    }
  }
}

class _PushPanel extends StatelessWidget {
  const _PushPanel({required this.ref});

  final WidgetRef ref;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const StatusBadge(
            label: 'Push movil',
            icon: Icons.notifications_active_rounded,
            color: AppColors.cyan,
          ),
          const SizedBox(height: 12),
          const Text(
            'Recibe avisos aunque Cardbook no este abierto',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 6),
          const Text(
            'Activa permisos para alianzas, tickets, actividad de tarjetas y eventos importantes.',
            style: TextStyle(color: AppColors.muted, height: 1.35),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: FilledButton.icon(
                  onPressed: () => _activatePush(context),
                  icon: const Icon(Icons.notifications_rounded),
                  label: const Text('Activar'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _sendTest(context),
                  icon: const Icon(Icons.send_rounded),
                  label: const Text('Prueba'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Future<void> _activatePush(BuildContext context) async {
    final result =
        await ref.read(pushNotificationControllerProvider).registerDevice();
    if (!context.mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(result.message)));
  }

  Future<void> _sendTest(BuildContext context) async {
    final result =
        await ref.read(pushNotificationControllerProvider).sendTest();
    if (!context.mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(result.message)));
  }
}

class _NotificationTile extends ConsumerWidget {
  const _NotificationTile({required this.item});

  final Map<String, dynamic> item;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isRead = item['is_read'] == true;
    final title = _text(item['title'], fallback: 'Notificacion Cardbook');
    final message = _text(item['message']);
    final eventType = _text(item['event_type'], fallback: 'cardbook');
    final createdAt = _formatDate(item['created_at']);

    return InkWell(
      onTap: isRead ? null : () => _markRead(context, ref),
      borderRadius: BorderRadius.circular(AppRadius.md),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isRead
              ? AppColors.inkAlt.withValues(alpha: .58)
              : AppColors.purple.withValues(alpha: .16),
          borderRadius: BorderRadius.circular(AppRadius.md),
          border:
              Border.all(color: isRead ? AppColors.stroke : AppColors.purple),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: _eventColor(eventType).withValues(alpha: .16),
                borderRadius: BorderRadius.circular(15),
              ),
              child: Icon(_eventIcon(eventType), color: _eventColor(eventType)),
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
                          title,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontWeight: FontWeight.w900),
                        ),
                      ),
                      if (!isRead)
                        Container(
                          width: 8,
                          height: 8,
                          decoration: const BoxDecoration(
                            color: AppColors.gold,
                            shape: BoxShape.circle,
                          ),
                        ),
                    ],
                  ),
                  if (message.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(
                      message,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                          color: AppColors.muted, fontSize: 12, height: 1.35),
                    ),
                  ],
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      StatusBadge(
                          label: _eventLabel(eventType),
                          color: _eventColor(eventType)),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          createdAt,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                              color: AppColors.muted, fontSize: 11),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _markRead(BuildContext context, WidgetRef ref) async {
    final id = _intValue(item['id']);
    if (id == null) return;
    try {
      await ref.read(notificationRepositoryProvider).markRead(id);
      ref.invalidate(referralNotificationsProvider);
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No pudimos marcar como leida.')),
        );
      }
    }
  }
}

class _AllianceSummary extends StatelessWidget {
  const _AllianceSummary({required this.items});

  final List<Map<String, dynamic>> items;

  @override
  Widget build(BuildContext context) {
    final pending = items.where((item) => item['status'] == 'pending').length;
    final accepted = items.where((item) => item['status'] == 'accepted').length;
    final rejected = items.where((item) => item['status'] == 'rejected').length;

    if (items.isEmpty) {
      return const AsyncStateView.empty(
        'No tienes solicitudes ni alianzas recientes.',
        title: 'Sin alianzas pendientes',
        icon: Icons.handshake_outlined,
      );
    }

    return Column(
      children: [
        Row(
          children: [
            Expanded(
                child: _SummaryPill(
                    label: 'Pendientes',
                    value: '$pending',
                    color: AppColors.gold)),
            const SizedBox(width: 8),
            Expanded(
                child: _SummaryPill(
                    label: 'Activas',
                    value: '$accepted',
                    color: AppColors.green)),
            const SizedBox(width: 8),
            Expanded(
                child: _SummaryPill(
                    label: 'Cerradas',
                    value: '$rejected',
                    color: AppColors.red)),
          ],
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: () => context.push('/alliances'),
          icon: const Icon(Icons.handshake_rounded),
          label: const Text('Abrir centro de alianzas'),
        ),
      ],
    );
  }
}

class _SummaryPill extends StatelessWidget {
  const _SummaryPill(
      {required this.label, required this.value, required this.color});

  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: .12),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: color.withValues(alpha: .32)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(value,
              style: TextStyle(
                  color: color, fontSize: 20, fontWeight: FontWeight.w900)),
          const SizedBox(height: 3),
          Text(label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: AppColors.muted, fontSize: 11)),
        ],
      ),
    );
  }
}

class _NotificationsHero extends StatelessWidget {
  const _NotificationsHero({required this.unreadCount});

  final int unreadCount;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      gradient: AppGradients.cardGlow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          StatusBadge(
              label: unreadCount > 0 ? '$unreadCount sin leer' : 'Al dia',
              icon: Icons.notifications_active_rounded,
              color: unreadCount > 0 ? AppColors.gold : AppColors.green),
          const SizedBox(height: 16),
          const Text('Notificaciones',
              style: TextStyle(
                  fontSize: 32, height: 1.05, fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          const Text(
            'Actividad importante, comisiones, referidos y alianzas de tu red Cardbook.',
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

String _formatDate(dynamic value) {
  final date = DateTime.tryParse(value?.toString() ?? '');
  if (date == null) return '';
  return DateFormat('d MMM yyyy, h:mm a').format(date.toLocal());
}

IconData _eventIcon(String eventType) {
  if (eventType.contains('commission')) return Icons.payments_rounded;
  if (eventType.contains('paid')) return Icons.verified_rounded;
  if (eventType.contains('company')) return Icons.business_center_rounded;
  if (eventType.contains('sale')) return Icons.point_of_sale_rounded;
  if (eventType.contains('finance')) return Icons.account_balance_rounded;
  return Icons.notifications_rounded;
}

Color _eventColor(String eventType) {
  if (eventType.contains('commission')) return AppColors.gold;
  if (eventType.contains('paid')) return AppColors.green;
  if (eventType.contains('finance')) return AppColors.cyan;
  if (eventType.contains('sale')) return AppColors.purple;
  return AppColors.blue;
}

String _eventLabel(String eventType) {
  if (eventType.contains('commission')) return 'Comision';
  if (eventType.contains('paid')) return 'Pago';
  if (eventType.contains('company')) return 'Empresa';
  if (eventType.contains('sale')) return 'Venta';
  if (eventType.contains('finance')) return 'Finanzas';
  return 'Cardbook';
}
