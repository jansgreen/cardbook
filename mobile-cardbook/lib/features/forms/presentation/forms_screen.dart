import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/platform/native_actions.dart';
import 'package:mobile_cardbook/features/forms/data/forms_repository.dart';
import 'package:mobile_cardbook/features/home/data/mobile_bootstrap_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/section_header.dart';
import 'package:mobile_cardbook/shared/widgets/share_center.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class FormsScreen extends ConsumerStatefulWidget {
  const FormsScreen({super.key});

  @override
  ConsumerState<FormsScreen> createState() => _FormsScreenState();
}

class _FormsScreenState extends ConsumerState<FormsScreen> {
  final _search = TextEditingController();

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final payload = ref.watch(mobileFormsPayloadProvider);
    final bootstrap = ref.watch(mobileBootstrapProvider).valueOrNull;
    final canManage = bootstrap?.can('can_manage_forms') ?? false;

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(mobileFormsPayloadProvider);
              ref.invalidate(mobileFormsProvider);
              await ref.read(mobileFormsPayloadProvider.future);
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
              children: [
                const BrandHeader(),
                const SizedBox(height: 24),
                _FormsHero(canManage: canManage),
                const SizedBox(height: 18),
                TextField(
                  controller: _search,
                  onChanged: (_) => setState(() {}),
                  decoration: const InputDecoration(
                    hintText: 'Buscar formulario, empresa o correo',
                    prefixIcon: Icon(Icons.search_rounded),
                  ),
                ),
                const SizedBox(height: 18),
                payload.when(
                  loading: () => const SizedBox(
                      height: 260, child: AsyncStateView.loading()),
                  error: (_, __) => AsyncStateView.error(
                    'No pudimos cargar tus formularios.',
                    actionLabel: 'Reintentar',
                    onAction: () => ref.invalidate(mobileFormsPayloadProvider),
                  ),
                  data: (data) {
                    final forms = _filter(data.forms);
                    final activeCount = data.forms
                        .where((item) => item['is_active'] == true)
                        .length;
                    final submissions = data.forms.fold<int>(
                      0,
                      (sum, item) => sum + _int(item['submission_count']),
                    );
                    return Column(
                      children: [
                        _FormsSummary(
                          total: data.forms.length,
                          active: activeCount,
                          submissions: submissions,
                          builderHome: data.builderHome,
                          canManage: canManage,
                        ),
                        const SizedBox(height: 18),
                        GlassCard(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              SectionHeader(
                                title: 'Formularios',
                                actionLabel: canManage ? 'Builder' : null,
                                onAction: canManage &&
                                        data.builderHome.isNotEmpty
                                    ? () =>
                                        NativeActions.website(data.builderHome)
                                    : null,
                              ),
                              const SizedBox(height: 12),
                              if (forms.isEmpty)
                                AsyncStateView.empty(
                                  data.forms.isEmpty
                                      ? 'Crea formularios para recibir mensajes, cotizaciones o solicitudes desde tus websites.'
                                      : 'No hay formularios que coincidan con tu busqueda.',
                                  title: data.forms.isEmpty
                                      ? 'Sin formularios'
                                      : 'Sin resultados',
                                  icon: Icons.dynamic_form_rounded,
                                  actionLabel:
                                      canManage ? 'Abrir builder' : null,
                                  onAction:
                                      canManage && data.builderHome.isNotEmpty
                                          ? () => NativeActions.website(
                                              data.builderHome)
                                          : null,
                                )
                              else
                                Column(
                                  children: [
                                    for (final form in forms) ...[
                                      _FormTile(
                                        form: form,
                                        canManageGlobal: canManage,
                                      ),
                                      const SizedBox(height: 12),
                                    ],
                                  ],
                                ),
                            ],
                          ),
                        ),
                      ],
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: null),
    );
  }

  List<Map<String, dynamic>> _filter(List<Map<String, dynamic>> forms) {
    final query = _search.text.trim().toLowerCase();
    if (query.isEmpty) return forms;
    return forms.where((form) {
      final haystack = [
        form['name'],
        form['company_name'],
        form['recipient_email'],
        form['description'],
      ].map(_text).join(' ').toLowerCase();
      return haystack.contains(query);
    }).toList();
  }
}

class _FormsSummary extends StatelessWidget {
  const _FormsSummary({
    required this.total,
    required this.active,
    required this.submissions,
    required this.builderHome,
    required this.canManage,
  });

  final int total;
  final int active;
  final int submissions;
  final String builderHome;
  final bool canManage;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(title: 'Centro de formularios'),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: _MetricPill(
                  label: 'Forms',
                  value: total.toString(),
                  icon: Icons.dynamic_form_rounded,
                  color: AppColors.cyan,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _MetricPill(
                  label: 'Activos',
                  value: active.toString(),
                  icon: Icons.check_circle_rounded,
                  color: AppColors.green,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _MetricPill(
                  label: 'Mensajes',
                  value: submissions.toString(),
                  icon: Icons.mark_email_read_rounded,
                  color: AppColors.gold,
                ),
              ),
            ],
          ),
          if (canManage && builderHome.isNotEmpty) ...[
            const SizedBox(height: 14),
            FilledButton.icon(
              onPressed: () => NativeActions.website(builderHome),
              icon: const Icon(Icons.tune_rounded),
              label: const Text('Administrar formularios'),
            ),
          ],
        ],
      ),
    );
  }
}

class _MetricPill extends StatelessWidget {
  const _MetricPill({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  final String label;
  final String value;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: .1),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: color.withValues(alpha: .26)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 8),
          Text(value,
              style:
                  const TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
          Text(label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: AppColors.muted, fontSize: 11)),
        ],
      ),
    );
  }
}

class _FormTile extends StatelessWidget {
  const _FormTile({
    required this.form,
    required this.canManageGlobal,
  });

  final Map<String, dynamic> form;
  final bool canManageGlobal;

  @override
  Widget build(BuildContext context) {
    final title = _text(form['name'], fallback: 'Formulario');
    final company = _text(form['company_name'], fallback: 'Empresa');
    final description = _text(form['description'],
        fallback: 'Formulario para recibir informacion de clientes.');
    final publicUrl = _text(form['public_url']);
    final dashboardUrl = _text(form['dashboard_url']);
    final email = _text(form['recipient_email']);
    final fields = _items(form['fields']);
    final active = form['is_active'] == true;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.inkAlt.withValues(alpha: .72),
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(
          color: active
              ? AppColors.green.withValues(alpha: .32)
              : AppColors.gold.withValues(alpha: .32),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 54,
                height: 54,
                decoration: BoxDecoration(
                  color: AppColors.purple.withValues(alpha: .18),
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(
                      color: AppColors.purple.withValues(alpha: .32)),
                ),
                child: const Icon(Icons.dynamic_form_rounded,
                    color: AppColors.purple),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            fontSize: 17, fontWeight: FontWeight.w900)),
                    const SizedBox(height: 4),
                    Text(company,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            color: AppColors.muted, fontSize: 12)),
                  ],
                ),
              ),
              StatusBadge(
                label: active ? 'Activo' : 'Pausado',
                icon: active
                    ? Icons.check_circle_rounded
                    : Icons.pause_circle_rounded,
                color: active ? AppColors.green : AppColors.gold,
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(description,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: AppColors.muted, height: 1.4)),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: _TinyStat(
                    label: 'Campos',
                    value: _text(form['field_count'], fallback: '0')),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _TinyStat(
                    label: 'Mensajes',
                    value: _text(form['submission_count'], fallback: '0')),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _TinyStat(
                    label: 'Email', value: email.isEmpty ? 'No' : 'Si'),
              ),
            ],
          ),
          if (fields.isNotEmpty) ...[
            const SizedBox(height: 14),
            const Text('Campos del formulario',
                style: TextStyle(fontWeight: FontWeight.w900, fontSize: 13)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final field in fields.take(8))
                  _FieldChip(
                    label: _text(field['label'], fallback: 'Campo'),
                    type: _text(field['field_type'], fallback: 'text'),
                    required: field['is_required'] == true,
                  ),
              ],
            ),
          ],
          const SizedBox(height: 14),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              _ActionChipButton(
                label: 'Abrir',
                icon: Icons.open_in_new_rounded,
                enabled: publicUrl.isNotEmpty,
                onTap: () => NativeActions.website(publicUrl),
              ),
              _ActionChipButton(
                label: 'Compartir',
                icon: Icons.ios_share_rounded,
                enabled: publicUrl.isNotEmpty,
                onTap: () => ShareCenter.show(
                  context,
                  SharePayload(
                    type: ShareTargetType.website,
                    title: title,
                    subtitle: 'Formulario de $company',
                    url: publicUrl,
                    email: email,
                    website: publicUrl,
                  ),
                ),
              ),
              _ActionChipButton(
                label: 'Editar',
                icon: Icons.edit_document,
                enabled: canManageGlobal && dashboardUrl.isNotEmpty,
                highlighted: true,
                onTap: () => NativeActions.website(dashboardUrl),
              ),
            ],
          ),
          if (email.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text('Recibe en $email',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: AppColors.muted, fontSize: 12)),
          ],
        ],
      ),
    );
  }
}

class _FieldChip extends StatelessWidget {
  const _FieldChip({
    required this.label,
    required this.type,
    required this.required,
  });

  final String label;
  final String type;
  final bool required;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.panelSoft.withValues(alpha: .72),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: AppColors.stroke),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label,
              style:
                  const TextStyle(fontSize: 12, fontWeight: FontWeight.w800)),
          const SizedBox(width: 6),
          Text(type.toUpperCase(),
              style: const TextStyle(color: AppColors.muted, fontSize: 10)),
          if (required) ...[
            const SizedBox(width: 4),
            const Text('*',
                style: TextStyle(color: AppColors.gold, fontSize: 12)),
          ],
        ],
      ),
    );
  }
}

class _TinyStat extends StatelessWidget {
  const _TinyStat({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
      decoration: BoxDecoration(
        color: AppColors.panelSoft.withValues(alpha: .72),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.stroke),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(value,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontWeight: FontWeight.w900)),
          Text(label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: AppColors.muted, fontSize: 10)),
        ],
      ),
    );
  }
}

class _ActionChipButton extends StatelessWidget {
  const _ActionChipButton({
    required this.label,
    required this.icon,
    required this.onTap,
    this.enabled = true,
    this.highlighted = false,
  });

  final String label;
  final IconData icon;
  final VoidCallback onTap;
  final bool enabled;
  final bool highlighted;

  @override
  Widget build(BuildContext context) {
    final color = highlighted ? AppColors.purple : AppColors.text;
    return InkWell(
      onTap: enabled ? onTap : null,
      borderRadius: BorderRadius.circular(999),
      child: Opacity(
        opacity: enabled ? 1 : .42,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 10),
          decoration: BoxDecoration(
            color: highlighted
                ? AppColors.purple.withValues(alpha: .2)
                : AppColors.panelSoft.withValues(alpha: .75),
            borderRadius: BorderRadius.circular(999),
            border: Border.all(color: color.withValues(alpha: .28)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 16, color: color),
              const SizedBox(width: 6),
              Text(label,
                  style: TextStyle(color: color, fontWeight: FontWeight.w900)),
            ],
          ),
        ),
      ),
    );
  }
}

class _FormsHero extends StatelessWidget {
  const _FormsHero({required this.canManage});

  final bool canManage;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      gradient: AppGradients.cardGlow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          StatusBadge(
            label: canManage ? 'Forms Builder habilitado' : 'Vista de forms',
            icon: Icons.dynamic_form_rounded,
            color: canManage ? AppColors.green : AppColors.gold,
          ),
          const SizedBox(height: 16),
          const Text('Forms Builder',
              style: TextStyle(
                  fontSize: 32, height: 1.05, fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          const Text(
            'Gestiona formularios de contacto, cotizacion y solicitudes conectados a las paginas publicas de tus empresas.',
            style: TextStyle(color: AppColors.muted, height: 1.45),
          ),
        ],
      ),
    );
  }
}

List<Map<String, dynamic>> _items(dynamic value) {
  if (value is! List) return const <Map<String, dynamic>>[];
  return value.whereType<Map<String, dynamic>>().toList();
}

String _text(dynamic value, {String fallback = ''}) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
}

int _int(dynamic value) {
  if (value is int) return value;
  return int.tryParse(value?.toString() ?? '') ?? 0;
}
