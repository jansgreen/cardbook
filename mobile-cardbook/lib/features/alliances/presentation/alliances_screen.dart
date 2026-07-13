import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/companies/data/companies_repository.dart';
import 'package:mobile_cardbook/features/notifications/data/notifications_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/section_header.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class AlliancesScreen extends ConsumerStatefulWidget {
  const AlliancesScreen({super.key});

  @override
  ConsumerState<AlliancesScreen> createState() => _AlliancesScreenState();
}

class _AlliancesScreenState extends ConsumerState<AlliancesScreen> {
  String _filter = 'all';

  @override
  Widget build(BuildContext context) {
    final alliances = ref.watch(alliancesProvider);
    final companies = ref.watch(companiesProvider);

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(alliancesProvider);
              ref.invalidate(companiesProvider);
              await Future.wait([
                ref.read(alliancesProvider.future),
                ref.read(companiesProvider.future),
              ]);
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
              children: [
                const BrandHeader(),
                const SizedBox(height: 24),
                const _AlliancesHero(),
                const SizedBox(height: 18),
                GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      SectionHeader(
                        title: 'Centro de alianzas',
                        actionLabel: 'Buscar empresas',
                        onAction: () => context.push('/companies'),
                      ),
                      const SizedBox(height: 12),
                      _AllianceFilters(
                        value: _filter,
                        onChanged: (value) => setState(() => _filter = value),
                      ),
                      const SizedBox(height: 14),
                      companies.when(
                        loading: () => const SizedBox(
                          height: 140,
                          child: AsyncStateView.loading(),
                        ),
                        error: (_, __) => const AsyncStateView.error(
                            'No pudimos cargar tus empresas.'),
                        data: (myCompanies) {
                          final myCompanyIds = myCompanies
                              .map((item) => _intValue(item['id']))
                              .whereType<int>()
                              .toSet();
                          return alliances.when(
                            loading: () => const SizedBox(
                              height: 140,
                              child: AsyncStateView.loading(),
                            ),
                            error: (_, __) => const AsyncStateView.error(
                                'No pudimos cargar tus alianzas.'),
                            data: (items) {
                              final filtered =
                                  _filtered(items, myCompanyIds, _filter);
                              if (filtered.isEmpty) {
                                return const AsyncStateView.empty(
                                  'No hay alianzas para este filtro todavia.',
                                );
                              }
                              return Column(
                                children: [
                                  for (final item in filtered) ...[
                                    _AllianceTile(
                                      item: item,
                                      myCompanyIds: myCompanyIds,
                                    ),
                                    const SizedBox(height: 10),
                                  ],
                                ],
                              );
                            },
                          );
                        },
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

  List<Map<String, dynamic>> _filtered(
    List<Map<String, dynamic>> items,
    Set<int> myCompanyIds,
    String filter,
  ) {
    return items.where((item) {
      final status = _text(item['status'], fallback: 'pending');
      final requesterId = _intValue(item['requester']);
      final receiverId = _intValue(item['receiver']);
      final isReceived =
          receiverId != null && myCompanyIds.contains(receiverId);
      final isSent = requesterId != null && myCompanyIds.contains(requesterId);

      switch (filter) {
        case 'received':
          return isReceived;
        case 'sent':
          return isSent;
        case 'pending':
          return status == 'pending';
        case 'accepted':
          return status == 'accepted';
        default:
          return true;
      }
    }).toList();
  }
}

class _AllianceFilters extends StatelessWidget {
  const _AllianceFilters({required this.value, required this.onChanged});

  final String value;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    final filters = const [
      ('all', 'Todas'),
      ('received', 'Recibidas'),
      ('sent', 'Enviadas'),
      ('pending', 'Pendientes'),
      ('accepted', 'Activas'),
    ];

    return SizedBox(
      height: 42,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemBuilder: (context, index) {
          final filter = filters[index];
          final active = filter.$1 == value;
          return ChoiceChip(
            selected: active,
            label: Text(filter.$2),
            onSelected: (_) => onChanged(filter.$1),
            selectedColor: AppColors.purple.withValues(alpha: .24),
            backgroundColor: AppColors.inkAlt.withValues(alpha: .72),
            side: BorderSide(
              color: active ? AppColors.purple : AppColors.stroke,
            ),
          );
        },
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemCount: filters.length,
      ),
    );
  }
}

class _AllianceTile extends ConsumerWidget {
  const _AllianceTile({required this.item, required this.myCompanyIds});

  final Map<String, dynamic> item;
  final Set<int> myCompanyIds;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final requester = item['requester_detail'] is Map<String, dynamic>
        ? item['requester_detail'] as Map<String, dynamic>
        : <String, dynamic>{};
    final receiver = item['receiver_detail'] is Map<String, dynamic>
        ? item['receiver_detail'] as Map<String, dynamic>
        : <String, dynamic>{};
    final status = _text(item['status'], fallback: 'pending');
    final requesterId = _intValue(item['requester']);
    final receiverId = _intValue(item['receiver']);
    final isReceived = receiverId != null && myCompanyIds.contains(receiverId);
    final isSent = requesterId != null && myCompanyIds.contains(requesterId);
    final requesterName = _text(requester['name'], fallback: 'Empresa');
    final receiverName = _text(receiver['name'], fallback: 'Empresa');

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.inkAlt.withValues(alpha: .72),
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
                  color: _statusColor(status).withValues(alpha: .14),
                  borderRadius: BorderRadius.circular(16),
                ),
                child:
                    Icon(Icons.handshake_rounded, color: _statusColor(status)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '$requesterName + $receiverName',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w900),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _directionLabel(isReceived: isReceived, isSent: isSent),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style:
                          const TextStyle(color: AppColors.muted, fontSize: 12),
                    ),
                  ],
                ),
              ),
              StatusBadge(
                label: _statusLabel(status),
                color: _statusColor(status),
              ),
            ],
          ),
          if (status == 'pending' && isReceived) ...[
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
          ] else if (status == 'pending' && isSent) ...[
            const SizedBox(height: 12),
            const Text(
              'Solicitud enviada. Esperando respuesta de la otra empresa.',
              style: TextStyle(color: AppColors.muted, fontSize: 12),
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _decide(
      BuildContext context, WidgetRef ref, String decision) async {
    final id = _intValue(item['id']);
    if (id == null) return;
    try {
      await ref
          .read(allianceRepositoryProvider)
          .decide(allianceId: id, decision: decision);
      ref.invalidate(alliancesProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(decision == 'accepted'
                ? 'Alianza aceptada.'
                : 'Alianza rechazada.'),
          ),
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
}

class _AlliancesHero extends StatelessWidget {
  const _AlliancesHero();

  @override
  Widget build(BuildContext context) {
    return const GlassCard(
      gradient: AppGradients.cardGlow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          StatusBadge(
              label: 'Red empresarial',
              icon: Icons.handshake_rounded,
              color: AppColors.gold),
          SizedBox(height: 16),
          Text('Alianzas',
              style: TextStyle(
                  fontSize: 32, height: 1.05, fontWeight: FontWeight.w900)),
          SizedBox(height: 8),
          Text(
            'Gestiona solicitudes, conexiones aceptadas y oportunidades entre empresas.',
            style: TextStyle(color: AppColors.muted, height: 1.45),
          ),
        ],
      ),
    );
  }
}

String _directionLabel({required bool isReceived, required bool isSent}) {
  if (isReceived && isSent) return 'Alianza entre tus empresas';
  if (isReceived) return 'Solicitud recibida';
  if (isSent) return 'Solicitud enviada';
  return 'Alianza relacionada';
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

String _text(dynamic value, {String fallback = ''}) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
}

int? _intValue(dynamic value) {
  if (value is int) return value;
  return int.tryParse(value?.toString() ?? '');
}
