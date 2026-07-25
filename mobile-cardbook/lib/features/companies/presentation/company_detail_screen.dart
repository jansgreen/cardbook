import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/core/config/api_config.dart';
import 'package:mobile_cardbook/core/platform/native_actions.dart';
import 'package:mobile_cardbook/features/book/data/book_repository.dart';
import 'package:mobile_cardbook/features/companies/data/companies_repository.dart';
import 'package:mobile_cardbook/features/home/data/mobile_bootstrap_repository.dart';
import 'package:mobile_cardbook/features/notifications/data/notifications_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/native_action_button.dart';
import 'package:mobile_cardbook/shared/widgets/share_center.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class CompanyDetailScreen extends ConsumerWidget {
  const CompanyDetailScreen({required this.company, super.key});

  final Map<String, dynamic> company;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final name = _text(company['name'], fallback: 'Empresa');
    final description =
        _text(company['description'], fallback: 'Empresa en Cardbook');
    final category = _text(company['category'], fallback: 'Negocio');
    final address = _text(company['address']);
    final city = _text(company['city']);
    final region = _text(company['region']);
    final website = _text(company['website']);
    final phone = _text(company['phone_number']);
    final email = _text(company['email']);
    final logo = _text(company['logo']);
    final slug = _text(company['slug']);
    final companyId = _intValue(company['id']);
    final bootstrap = ref.watch(mobileBootstrapProvider).valueOrNull;
    final canCreateDigital = bootstrap?.can('can_create_digital_card') ?? false;
    final canCreateBusiness =
        bootstrap?.can('can_create_business_card') ?? false;
    final canCreateCompany = bootstrap?.can('can_create_company') ?? false;
    final publicUrl = slug.isEmpty
        ? ApiConfig.publicBase
        : '${ApiConfig.publicBase}/business/$slug/';

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
            children: [
              Row(
                children: [
                  IconButton(
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.arrow_back_rounded),
                  ),
                  const Spacer(),
                  IconButton(
                    onPressed: () => ShareCenter.show(
                      context,
                      SharePayload(
                        type: ShareTargetType.company,
                        title: name,
                        subtitle: description,
                        url: publicUrl,
                        phone: phone,
                        email: email,
                        website: website,
                        address: address,
                        organization: name,
                      ),
                    ),
                    icon: const Icon(Icons.share_rounded),
                  ),
                  if (canCreateCompany)
                    IconButton(
                      onPressed: () =>
                          context.push('/companies/form', extra: company),
                      icon: const Icon(Icons.edit_rounded),
                    ),
                ],
              ),
              const SizedBox(height: 12),
              GlassCard(
                padding: const EdgeInsets.all(20),
                gradient: AppGradients.cardGlow,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _Logo(url: logo, name: name),
                    const SizedBox(height: 18),
                    StatusBadge(
                        label: category,
                        icon: Icons.verified_rounded,
                        color: AppColors.gold),
                    const SizedBox(height: 16),
                    Text(name,
                        style: const TextStyle(
                            fontSize: 30,
                            height: 1.05,
                            fontWeight: FontWeight.w900)),
                    const SizedBox(height: 10),
                    Text(description,
                        style: const TextStyle(
                            color: AppColors.muted, height: 1.45)),
                    if (city.isNotEmpty || region.isNotEmpty) ...[
                      const SizedBox(height: 14),
                      Row(
                        children: [
                          const Icon(Icons.location_on_outlined,
                              color: AppColors.muted, size: 18),
                          const SizedBox(width: 6),
                          Expanded(
                              child: Text(_join([city, region]),
                                  style:
                                      const TextStyle(color: AppColors.muted))),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 18),
              GlassCard(
                child: Wrap(
                  spacing: 10,
                  runSpacing: 10,
                  children: [
                    _ActionSlot(
                        child: NativeActionButton(
                            icon: Icons.call_rounded,
                            label: 'Llamar',
                            onTap: () => NativeActions.call(phone))),
                    _ActionSlot(
                        child: NativeActionButton(
                            icon: Icons.email_rounded,
                            label: 'Email',
                            onTap: () =>
                                NativeActions.email(email, subject: name))),
                    _ActionSlot(
                        child: NativeActionButton(
                            icon: Icons.language_rounded,
                            label: 'Web',
                            onTap: () => NativeActions.website(website))),
                    _ActionSlot(
                        child: NativeActionButton(
                            icon: Icons.map_rounded,
                            label: 'Mapa',
                            onTap: () => NativeActions.maps(address))),
                    _ActionSlot(
                      child: NativeActionButton(
                        icon: Icons.share_rounded,
                        label: 'Compartir',
                        color: AppColors.gold,
                        onTap: () => ShareCenter.show(
                          context,
                          SharePayload(
                            type: ShareTargetType.company,
                            title: name,
                            subtitle: description,
                            url: publicUrl,
                            phone: phone,
                            email: email,
                            website: website,
                            address: address,
                            organization: name,
                          ),
                        ),
                      ),
                    ),
                    _ActionSlot(
                      child: NativeActionButton(
                        icon: Icons.contact_page_rounded,
                        label: 'Contacto',
                        color: AppColors.green,
                        onTap: () => NativeActions.shareContactCard(
                          name: name,
                          organization: name,
                          phone: phone,
                          email: email,
                          website: website.isNotEmpty ? website : publicUrl,
                          address: address,
                          note: description,
                        ),
                      ),
                    ),
                    if (canCreateDigital)
                      _ActionSlot(
                        child: NativeActionButton(
                          icon: Icons.badge_rounded,
                          label: 'Crear perfil',
                          color: AppColors.blue,
                          onTap: () => context.push('/cards/digital/form',
                              extra: {'initialCompany': company}),
                        ),
                      ),
                    if (canCreateBusiness)
                      _ActionSlot(
                        child: NativeActionButton(
                          icon: Icons.contact_mail_rounded,
                          label: 'Crear tarjeta',
                          color: AppColors.gold,
                          onTap: () => context.push('/cards/business/form',
                              extra: {'initialCompany': company}),
                        ),
                      ),
                    _ActionSlot(
                      child: NativeActionButton(
                        icon: Icons.open_in_new_rounded,
                        label: 'Publico',
                        color: AppColors.green,
                        onTap: () => NativeActions.website(publicUrl),
                      ),
                    ),
                    _ActionSlot(
                      child: NativeActionButton(
                        icon: Icons.bookmark_add_rounded,
                        label: 'Guardar',
                        color: AppColors.purple,
                        onTap: companyId == null
                            ? () {}
                            : () => _saveToBook(context, ref, companyId),
                      ),
                    ),
                    _ActionSlot(
                      child: NativeActionButton(
                        icon: Icons.handshake_rounded,
                        label: 'Alianza',
                        color: AppColors.cyan,
                        onTap: companyId == null
                            ? () {}
                            : () => _requestAlliance(context, ref, companyId),
                      ),
                    ),
                    if (canCreateCompany)
                      _ActionSlot(
                        child: NativeActionButton(
                          icon: Icons.delete_outline_rounded,
                          label: 'Eliminar',
                          color: AppColors.red,
                          onTap: () => _confirmDelete(context, ref, name),
                        ),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 18),
              GlassCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Informacion',
                        style: TextStyle(
                            fontSize: 16, fontWeight: FontWeight.w900)),
                    const SizedBox(height: 12),
                    _InfoRow(label: 'Telefono', value: phone),
                    _InfoRow(label: 'Email', value: email),
                    _InfoRow(label: 'Website', value: website),
                    _InfoRow(label: 'Direccion', value: address),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _saveToBook(
      BuildContext context, WidgetRef ref, int companyId) async {
    try {
      await ref.read(bookRepositoryProvider).saveCompany(companyId);
      ref.invalidate(bookProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Guardado en Book.')),
        );
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No pudimos guardar este negocio.')),
        );
      }
    }
  }

  Future<void> _requestAlliance(
      BuildContext context, WidgetRef ref, int receiverId) async {
    final companies = await ref.read(companiesProvider.future);
    if (!context.mounted) return;
    final available =
        companies.where((item) => _intValue(item['id']) != receiverId).toList();
    if (available.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content:
                Text('Necesitas una empresa propia para solicitar alianza.')),
      );
      return;
    }

    final requesterId = await showModalBottomSheet<int>(
      context: context,
      backgroundColor: AppColors.panel,
      builder: (sheetContext) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Solicitar alianza desde',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
              const SizedBox(height: 12),
              for (final item in available)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(_text(item['name'], fallback: 'Empresa')),
                  subtitle: Text(
                      _text(item['category'], fallback: 'Empresa Cardbook')),
                  onTap: () =>
                      Navigator.of(sheetContext).pop(_intValue(item['id'])),
                ),
            ],
          ),
        ),
      ),
    );

    if (requesterId == null || !context.mounted) return;
    try {
      await ref
          .read(allianceRepositoryProvider)
          .requestAlliance(requesterId: requesterId, receiverId: receiverId);
      ref.invalidate(alliancesProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Solicitud de alianza enviada.')),
        );
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No pudimos solicitar la alianza.')),
        );
      }
    }
  }

  Future<void> _confirmDelete(
      BuildContext context, WidgetRef ref, String name) async {
    final id = company['id'];
    if (id is! int) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: AppColors.panel,
        title: const Text('Eliminar empresa'),
        content:
            Text('Quieres eliminar $name? Esta accion desactivara la empresa.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(false),
              child: const Text('Cancelar')),
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child:
                const Text('Eliminar', style: TextStyle(color: AppColors.red)),
          ),
        ],
      ),
    );
    if (confirmed != true || !context.mounted) return;
    try {
      await ref.read(companyRepositoryProvider).delete(id);
      ref.invalidate(companiesProvider);
      ref.invalidate(recommendedCompaniesProvider);
      if (context.mounted) context.go('/companies');
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No pudimos eliminar la empresa.')),
        );
      }
    }
  }
}

class _ActionSlot extends StatelessWidget {
  const _ActionSlot({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
        width: (MediaQuery.sizeOf(context).width - 70) / 2, child: child);
  }
}

class _Logo extends StatelessWidget {
  const _Logo({required this.url, required this.name});

  final String url;
  final String name;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 82,
      height: 82,
      decoration: BoxDecoration(
        color: AppColors.panelSoft,
        borderRadius: BorderRadius.circular(26),
        border: Border.all(color: AppColors.stroke),
      ),
      clipBehavior: Clip.antiAlias,
      child: url.isEmpty
          ? Center(
              child: Text(_initials(name),
                  style: const TextStyle(
                      fontWeight: FontWeight.w900, fontSize: 20)))
          : Image.network(
              url,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => Center(
                  child: Text(_initials(name),
                      style: const TextStyle(fontWeight: FontWeight.w900))),
            ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    if (value.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
              width: 88,
              child: Text(label,
                  style:
                      const TextStyle(color: AppColors.muted, fontSize: 12))),
          Expanded(
              child: Text(value,
                  style: const TextStyle(fontWeight: FontWeight.w800))),
        ],
      ),
    );
  }
}

String _text(dynamic value, {String fallback = ''}) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
}

String _join(List<String> values) {
  return values.where((value) => value.trim().isNotEmpty).join(', ');
}

String _initials(String value) {
  final words = value
      .trim()
      .split(RegExp(r'\s+'))
      .where((word) => word.isNotEmpty)
      .toList();
  if (words.isEmpty) {
    return 'CB';
  }
  if (words.length == 1) {
    return words.first
        .substring(0, words.first.length >= 2 ? 2 : 1)
        .toUpperCase();
  }
  return '${words[0][0]}${words[1][0]}'.toUpperCase();
}

int? _intValue(dynamic value) {
  if (value is int) return value;
  return int.tryParse(value?.toString() ?? '');
}
