import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/core/config/api_config.dart';
import 'package:mobile_cardbook/core/platform/native_actions.dart';
import 'package:mobile_cardbook/features/cards/data/cards_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/native_action_button.dart';
import 'package:mobile_cardbook/shared/widgets/share_center.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class CardDetailScreen extends ConsumerWidget {
  const CardDetailScreen({
    required this.card,
    required this.kind,
    super.key,
  });

  final Map<String, dynamic> card;
  final String kind;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isBusinessCard = kind == 'business';
    final title = isBusinessCard
        ? _firstText([card['display_name']],
            fallback: 'Tarjeta de presentacion')
        : 'Perfil de negocio';
    final companyName = _text(card['company_name']);
    final jobTitle = _text(card['job_title']);
    final subtitle = _firstText([companyName, jobTitle, card['email']],
        fallback: 'Cardbook');
    final phone = _text(card['phone_number']);
    final email = _text(card['email']);
    final website = _text(card['website']);
    final whatsapp =
        _firstText([card['whatsapp_url'], card['phone_number']], fallback: '');
    final slug = _text(card['slug']);
    final publicPath = isBusinessCard ? '/c/presentacion/$slug/' : '/c/$slug/';
    final publicUrl = slug.isEmpty
        ? ApiConfig.publicBase
        : '${ApiConfig.publicBase}$publicPath';

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
                        type: isBusinessCard
                            ? ShareTargetType.businessCard
                            : ShareTargetType.digitalCard,
                        title: title,
                        subtitle: subtitle,
                        url: publicUrl,
                        phone: phone,
                        email: email,
                        website: website,
                        organization: companyName,
                        jobTitle: jobTitle,
                      ),
                    ),
                    icon: const Icon(Icons.share_rounded),
                  ),
                  IconButton(
                    onPressed: () => context.push(
                        isBusinessCard
                            ? '/cards/business/form'
                            : '/cards/digital/form',
                        extra: card),
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
                    StatusBadge(
                      label: isBusinessCard ? 'Presentacion' : 'Perfil digital',
                      icon: isBusinessCard
                          ? Icons.contact_page_rounded
                          : Icons.badge_rounded,
                      color: AppColors.gold,
                    ),
                    const SizedBox(height: 18),
                    Text(title,
                        style: const TextStyle(
                            fontSize: 30,
                            height: 1.05,
                            fontWeight: FontWeight.w900)),
                    const SizedBox(height: 8),
                    Text(subtitle,
                        style: const TextStyle(
                            color: AppColors.muted, height: 1.45)),
                    if (slug.isNotEmpty) ...[
                      const SizedBox(height: 14),
                      Text(slug,
                          style: const TextStyle(
                              color: AppColors.purple,
                              fontWeight: FontWeight.w800)),
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
                                NativeActions.email(email, subject: title))),
                    _ActionSlot(
                        child: NativeActionButton(
                            icon: Icons.language_rounded,
                            label: 'Web',
                            onTap: () => NativeActions.website(website))),
                    _ActionSlot(
                      child: NativeActionButton(
                        icon: Icons.chat_rounded,
                        label: 'WhatsApp',
                        color: AppColors.green,
                        onTap: () => NativeActions.whatsapp(whatsapp),
                      ),
                    ),
                    _ActionSlot(
                      child: NativeActionButton(
                        icon: Icons.share_rounded,
                        label: 'Compartir',
                        color: AppColors.gold,
                        onTap: () => ShareCenter.show(
                          context,
                          SharePayload(
                            type: isBusinessCard
                                ? ShareTargetType.businessCard
                                : ShareTargetType.digitalCard,
                            title: title,
                            subtitle: subtitle,
                            url: publicUrl,
                            phone: phone,
                            email: email,
                            website: website,
                            organization: companyName,
                            jobTitle: jobTitle,
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
                          name: title,
                          organization: companyName,
                          jobTitle: jobTitle,
                          phone: phone,
                          email: email,
                          website: website.isNotEmpty ? website : publicUrl,
                          note: subtitle,
                        ),
                      ),
                    ),
                    _ActionSlot(
                      child: NativeActionButton(
                        icon: Icons.open_in_new_rounded,
                        label: 'Publico',
                        color: AppColors.purple,
                        onTap: () => NativeActions.website(publicUrl),
                      ),
                    ),
                    _ActionSlot(
                      child: NativeActionButton(
                        icon: Icons.delete_outline_rounded,
                        label: 'Eliminar',
                        color: AppColors.red,
                        onTap: () =>
                            _confirmDelete(context, ref, title, isBusinessCard),
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
                    const Text('Contacto',
                        style: TextStyle(
                            fontSize: 16, fontWeight: FontWeight.w900)),
                    const SizedBox(height: 12),
                    _InfoRow(label: 'Telefono', value: phone),
                    _InfoRow(label: 'Email', value: email),
                    _InfoRow(label: 'Website', value: website),
                    _InfoRow(label: 'Publico', value: publicUrl),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _confirmDelete(BuildContext context, WidgetRef ref, String title,
      bool isBusinessCard) async {
    final id = card['id'];
    if (id is! int) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: AppColors.panel,
        title: const Text('Eliminar tarjeta'),
        content: Text(
            'Quieres eliminar $title? Esta accion desactivara la tarjeta.'),
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
      final repository = ref.read(cardRepositoryProvider);
      if (isBusinessCard) {
        await repository.deleteBusiness(id);
        ref.invalidate(businessCardsProvider);
      } else {
        await repository.deleteDigital(id);
        ref.invalidate(digitalCardsProvider);
      }
      if (context.mounted) context.go('/cards');
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No pudimos eliminar la tarjeta.')),
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

String _text(dynamic value) => value?.toString().trim() ?? '';

String _firstText(List<dynamic> values, {required String fallback}) {
  for (final value in values) {
    final text = _text(value);
    if (text.isNotEmpty) return text;
  }
  return fallback;
}
