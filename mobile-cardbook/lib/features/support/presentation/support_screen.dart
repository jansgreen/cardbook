import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:mobile_cardbook/features/support/data/support_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class SupportScreen extends ConsumerStatefulWidget {
  const SupportScreen({super.key});

  @override
  ConsumerState<SupportScreen> createState() => _SupportScreenState();
}

class _SupportScreenState extends ConsumerState<SupportScreen> {
  final _formKey = GlobalKey<FormState>();
  final _subjectController = TextEditingController();
  final _messageController = TextEditingController();
  final _subjectFocus = FocusNode();
  String _category = 'mobile';
  String _priority = 'normal';
  bool _isSubmitting = false;

  @override
  void dispose() {
    _subjectController.dispose();
    _messageController.dispose();
    _subjectFocus.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final tickets = ref.watch(supportTicketsProvider);

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(supportTicketsProvider);
              await ref.read(supportTicketsProvider.future);
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
              children: [
                const BrandHeader(),
                const SizedBox(height: 24),
                GlassCard(
                  gradient: AppGradients.cardGlow,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const StatusBadge(
                        label: 'Soporte',
                        icon: Icons.support_agent_rounded,
                        color: AppColors.cyan,
                      ),
                      const SizedBox(height: 16),
                      const Text(
                        'Centro de soporte',
                        style: TextStyle(
                          fontSize: 32,
                          height: 1.05,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Reporta problemas de acceso, tarjetas, empresas, Book, pagos o funciones moviles.',
                        style: TextStyle(color: AppColors.muted, height: 1.45),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                _SupportForm(
                  formKey: _formKey,
                  subjectController: _subjectController,
                  messageController: _messageController,
                  subjectFocus: _subjectFocus,
                  category: _category,
                  priority: _priority,
                  isSubmitting: _isSubmitting,
                  onCategoryChanged: (value) => setState(() {
                    _category = value ?? _category;
                  }),
                  onPriorityChanged: (value) => setState(() {
                    _priority = value ?? _priority;
                  }),
                  onSubmit: _submit,
                ),
                const SizedBox(height: 18),
                GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Expanded(
                            child: Text(
                              'Tickets recientes',
                              style: TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.w900,
                              ),
                            ),
                          ),
                          TextButton.icon(
                            onPressed: () => context.push('/diagnostics'),
                            icon: const Icon(Icons.health_and_safety_rounded),
                            label: const Text('Diagnostico'),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      tickets.when(
                        loading: () => const SizedBox(
                          height: 140,
                          child: AsyncStateView.loading(),
                        ),
                        error: (_, __) => AsyncStateView.error(
                          'No pudimos cargar tus tickets.',
                          actionLabel: 'Reintentar',
                          onAction: () =>
                              ref.invalidate(supportTicketsProvider),
                        ),
                        data: (items) {
                          if (items.isEmpty) {
                            return AsyncStateView.empty(
                              'Cuando envies un reporte, podras darle seguimiento aqui.',
                              title: 'Sin tickets abiertos',
                              icon: Icons.support_agent_rounded,
                              actionLabel: 'Escribir reporte',
                              onAction: () => _subjectFocus.requestFocus(),
                            );
                          }
                          return Column(
                            children: [
                              for (final item in items) ...[
                                _TicketTile(ticket: item),
                                const SizedBox(height: 10),
                              ],
                            ],
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
      bottomNavigationBar: const AppBottomNav(currentIndex: 4),
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isSubmitting = true);
    try {
      await ref.read(supportRepositoryProvider).createTicket(
            category: _category,
            priority: _priority,
            subject: _subjectController.text.trim(),
            message: _messageController.text.trim(),
          );
      _subjectController.clear();
      _messageController.clear();
      ref.invalidate(supportTicketsProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Ticket enviado a soporte.')),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No pudimos enviar el ticket.')),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }
}

class _SupportForm extends StatelessWidget {
  const _SupportForm({
    required this.formKey,
    required this.subjectController,
    required this.messageController,
    required this.subjectFocus,
    required this.category,
    required this.priority,
    required this.isSubmitting,
    required this.onCategoryChanged,
    required this.onPriorityChanged,
    required this.onSubmit,
  });

  final GlobalKey<FormState> formKey;
  final TextEditingController subjectController;
  final TextEditingController messageController;
  final FocusNode subjectFocus;
  final String category;
  final String priority;
  final bool isSubmitting;
  final ValueChanged<String?> onCategoryChanged;
  final ValueChanged<String?> onPriorityChanged;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Form(
        key: formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Nuevo reporte',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
            ),
            const SizedBox(height: 14),
            DropdownButtonFormField<String>(
              initialValue: category,
              decoration: const InputDecoration(labelText: 'Categoria'),
              items: const [
                DropdownMenuItem(value: 'mobile', child: Text('App movil')),
                DropdownMenuItem(value: 'account', child: Text('Cuenta')),
                DropdownMenuItem(value: 'companies', child: Text('Empresas')),
                DropdownMenuItem(value: 'cards', child: Text('Tarjetas')),
                DropdownMenuItem(value: 'book', child: Text('Book')),
                DropdownMenuItem(value: 'alliances', child: Text('Alianzas')),
                DropdownMenuItem(value: 'billing', child: Text('Pagos')),
                DropdownMenuItem(
                    value: 'website', child: Text('Website Builder')),
                DropdownMenuItem(value: 'other', child: Text('Otro')),
              ],
              onChanged: onCategoryChanged,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: priority,
              decoration: const InputDecoration(labelText: 'Prioridad'),
              items: const [
                DropdownMenuItem(value: 'low', child: Text('Baja')),
                DropdownMenuItem(value: 'normal', child: Text('Normal')),
                DropdownMenuItem(value: 'high', child: Text('Alta')),
                DropdownMenuItem(value: 'urgent', child: Text('Urgente')),
              ],
              onChanged: onPriorityChanged,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: subjectController,
              focusNode: subjectFocus,
              decoration: const InputDecoration(
                labelText: 'Asunto',
                hintText: 'Ej: No puedo crear una tarjeta',
              ),
              textInputAction: TextInputAction.next,
              validator: (value) {
                final text = value?.trim() ?? '';
                if (text.length < 5) return 'Escribe un asunto mas claro.';
                return null;
              },
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: messageController,
              minLines: 5,
              maxLines: 8,
              decoration: const InputDecoration(
                labelText: 'Mensaje',
                hintText: 'Describe que paso, donde paso y que esperabas ver.',
              ),
              validator: (value) {
                final text = value?.trim() ?? '';
                if (text.length < 15) return 'Agrega mas detalle al reporte.';
                return null;
              },
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: isSubmitting ? null : onSubmit,
              icon: isSubmitting
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.send_rounded),
              label: Text(isSubmitting ? 'Enviando' : 'Enviar reporte'),
            ),
          ],
        ),
      ),
    );
  }
}

class _TicketTile extends StatelessWidget {
  const _TicketTile({required this.ticket});

  final Map<String, dynamic> ticket;

  @override
  Widget build(BuildContext context) {
    final priority = _text(ticket['priority'], fallback: 'normal');
    final status = _text(ticket['status'], fallback: 'open');
    final createdAt = _date(ticket['created_at']);
    final color = _statusColor(status);

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.inkAlt.withValues(alpha: .62),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.stroke),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  _text(ticket['subject'], fallback: 'Ticket Cardbook'),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.w900),
                ),
              ),
              StatusBadge(label: _statusLabel(status), color: color),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            _text(ticket['message']),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: AppColors.muted, height: 1.35),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              StatusBadge(
                  label: _priorityLabel(priority),
                  color: _priorityColor(priority)),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  createdAt,
                  textAlign: TextAlign.right,
                  style: const TextStyle(color: AppColors.muted, fontSize: 12),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

String _text(dynamic value, {String fallback = ''}) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
}

String _date(dynamic value) {
  final date = DateTime.tryParse(value?.toString() ?? '');
  if (date == null) return '';
  return DateFormat('d MMM yyyy, h:mm a').format(date.toLocal());
}

String _statusLabel(String value) {
  return switch (value) {
    'in_progress' => 'En proceso',
    'resolved' => 'Resuelto',
    'closed' => 'Cerrado',
    _ => 'Abierto',
  };
}

Color _statusColor(String value) {
  return switch (value) {
    'in_progress' => AppColors.gold,
    'resolved' => AppColors.green,
    'closed' => AppColors.muted,
    _ => AppColors.cyan,
  };
}

String _priorityLabel(String value) {
  return switch (value) {
    'low' => 'Baja',
    'high' => 'Alta',
    'urgent' => 'Urgente',
    _ => 'Normal',
  };
}

Color _priorityColor(String value) {
  return switch (value) {
    'low' => AppColors.green,
    'high' => AppColors.gold,
    'urgent' => AppColors.red,
    _ => AppColors.purple,
  };
}
