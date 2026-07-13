import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/core/config/api_config.dart';
import 'package:mobile_cardbook/core/config/app_version.dart';
import 'package:mobile_cardbook/core/platform/native_actions.dart';
import 'package:mobile_cardbook/features/auth/data/auth_repository.dart';
import 'package:mobile_cardbook/features/profile/data/profile_repository.dart';
import 'package:mobile_cardbook/features/updates/presentation/update_status_card.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profile = ref.watch(profileProvider);

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(profileProvider);
              await ref.read(profileProvider.future);
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
              children: [
                const BrandHeader(),
                const SizedBox(height: 24),
                profile.when(
                  loading: () => const SizedBox(
                      height: 220, child: AsyncStateView.loading()),
                  error: (_, __) => const AsyncStateView.error(
                      'No pudimos cargar tu perfil.'),
                  data: (data) => _ProfileContent(profile: data),
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

class _ProfileContent extends ConsumerWidget {
  const _ProfileContent({required this.profile});

  final Map<String, dynamic> profile;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final fullName = _fullName(profile);
    final username = _text(profile['username'], fallback: 'usuario');
    final email = _text(profile['email']);
    final phone = _text(profile['phone_number']);
    final language =
        _text(profile['preferred_language'], fallback: 'es').toUpperCase();
    final avatar = _text(profile['avatar']);

    return Column(
      children: [
        GlassCard(
          padding: const EdgeInsets.all(20),
          gradient: AppGradients.cardGlow,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _Avatar(name: fullName, avatarUrl: avatar),
              const SizedBox(height: 18),
              StatusBadge(
                  label: 'Cuenta Cardbook',
                  icon: Icons.verified_user_rounded,
                  color: AppColors.gold),
              const SizedBox(height: 16),
              Text(fullName,
                  style: const TextStyle(
                      fontSize: 30, height: 1.05, fontWeight: FontWeight.w900)),
              const SizedBox(height: 6),
              Text('@$username',
                  style: const TextStyle(
                      color: AppColors.purple, fontWeight: FontWeight.w800)),
              if (email.isNotEmpty) ...[
                const SizedBox(height: 12),
                _InfoLine(icon: Icons.email_rounded, value: email),
              ],
              if (phone.isNotEmpty) ...[
                const SizedBox(height: 8),
                _InfoLine(icon: Icons.call_rounded, value: phone),
              ],
              const SizedBox(height: 8),
              _InfoLine(
                  icon: Icons.translate_rounded, value: 'Idioma $language'),
            ],
          ),
        ),
        const SizedBox(height: 18),
        const UpdateStatusCard(),
        const SizedBox(height: 18),
        GlassCard(
          child: Column(
            children: [
              _ProfileAction(
                icon: Icons.edit_rounded,
                label: 'Editar perfil',
                onTap: () => context.push('/profile/edit', extra: profile),
              ),
              _ProfileAction(
                icon: Icons.bookmarks_rounded,
                label: 'Abrir Book',
                onTap: () => context.push('/book'),
              ),
              _ProfileAction(
                icon: Icons.work_outline_rounded,
                label: 'White Card Jobs',
                onTap: () => context.push('/jobs'),
              ),
              _ProfileAction(
                icon: Icons.handshake_rounded,
                label: 'Alianzas',
                onTap: () => context.push('/alliances'),
              ),
              _ProfileAction(
                icon: Icons.public_rounded,
                label: 'Website Builder',
                onTap: () => context.push('/websites'),
              ),
              _ProfileAction(
                icon: Icons.notifications_rounded,
                label: 'Notificaciones',
                onTap: () => context.push('/notifications'),
              ),
              _ProfileAction(
                icon: Icons.health_and_safety_rounded,
                label: 'Diagnostico movil',
                onTap: () => context.push('/diagnostics'),
              ),
              _ProfileAction(
                icon: Icons.support_agent_rounded,
                label: 'Soporte',
                onTap: () => context.push('/support'),
              ),
              _ProfileAction(
                icon: Icons.logout_rounded,
                label: 'Cerrar sesion',
                color: AppColors.red,
                onTap: () => _confirmLogout(context, ref),
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        _QuickActionGrid(profile: profile),
        const SizedBox(height: 18),
        const _AccountStatusPanel(),
        const SizedBox(height: 18),
        const _SupportPanel(),
      ],
    );
  }

  Future<void> _confirmLogout(BuildContext context, WidgetRef ref) async {
    final shouldLogout = await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Cerrar sesion'),
            content: const Text(
                'Tu sesion se cerrara en este dispositivo. Podras volver a entrar con tu usuario y contrasena.'),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(false),
                child: const Text('Cancelar'),
              ),
              FilledButton(
                onPressed: () => Navigator.of(context).pop(true),
                child: const Text('Cerrar sesion'),
              ),
            ],
          ),
        ) ??
        false;

    if (!context.mounted) return;
    if (shouldLogout) await _logout(context, ref);
  }

  Future<void> _logout(BuildContext context, WidgetRef ref) async {
    await ref.read(authRepositoryProvider).logout();
    ref.invalidate(profileProvider);
    if (context.mounted) context.go('/login');
  }
}

class _QuickActionGrid extends StatelessWidget {
  const _QuickActionGrid({required this.profile});

  final Map<String, dynamic> profile;

  @override
  Widget build(BuildContext context) {
    final fullName = _fullName(profile);
    final email = _text(profile['email']);
    final phone = _text(profile['phone_number']);

    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Acciones de cuenta',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
          const SizedBox(height: 12),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 10,
            mainAxisSpacing: 10,
            childAspectRatio: 1.45,
            children: [
              _QuickActionTile(
                icon: Icons.person_add_alt_1_rounded,
                label: 'Compartir contacto',
                color: AppColors.green,
                onTap: () => NativeActions.shareContactCard(
                  name: fullName,
                  phone: phone,
                  email: email,
                  website: ApiConfig.publicBase,
                  note: 'Perfil de usuario Cardbook',
                ),
              ),
              _QuickActionTile(
                icon: Icons.copy_rounded,
                label: 'Copiar API',
                color: AppColors.cyan,
                onTap: () async {
                  await NativeActions.copyText(ApiConfig.publicBase);
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('URL copiada')),
                    );
                  }
                },
              ),
              _QuickActionTile(
                icon: Icons.public_rounded,
                label: 'Abrir web',
                color: AppColors.blue,
                onTap: () => NativeActions.website(ApiConfig.publicBase),
              ),
              _QuickActionTile(
                icon: Icons.mail_rounded,
                label: 'Soporte',
                color: AppColors.gold,
                onTap: () => NativeActions.email(
                  'support@cardbook.app',
                  subject: 'Soporte Cardbook movil',
                  body: 'Hola, necesito ayuda con mi cuenta Cardbook.',
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _QuickActionTile extends StatelessWidget {
  const _QuickActionTile({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppRadius.md),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: color.withValues(alpha: .12),
          borderRadius: BorderRadius.circular(AppRadius.md),
          border: Border.all(color: color.withValues(alpha: .28)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Icon(icon, color: color),
            Text(label,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontWeight: FontWeight.w900)),
          ],
        ),
      ),
    );
  }
}

class _AccountStatusPanel extends StatelessWidget {
  const _AccountStatusPanel();

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: const [
          Text('Estado de la app',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
          SizedBox(height: 14),
          _StatusRow(
            icon: Icons.cloud_done_rounded,
            label: 'API conectada',
            value: ApiConfig.baseUrl,
          ),
          _StatusRow(
            icon: Icons.security_rounded,
            label: 'Sesion',
            value: 'Protegida con token JWT',
          ),
          _StatusRow(
            icon: Icons.system_update_alt_rounded,
            label: 'Version',
            value: '${AppVersion.name} (${AppVersion.code})',
          ),
          _StatusRow(
            icon: Icons.android_rounded,
            label: 'Paquete',
            value: AppVersion.packageName,
          ),
        ],
      ),
    );
  }
}

class _StatusRow extends StatelessWidget {
  const _StatusRow({
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
                const SizedBox(height: 2),
                Text(value,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
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

class _SupportPanel extends StatelessWidget {
  const _SupportPanel();

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      gradient: AppGradients.cardGlow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const StatusBadge(
              label: 'Ayuda',
              icon: Icons.support_agent_rounded,
              color: AppColors.cyan),
          const SizedBox(height: 14),
          const Text('Centro de soporte Cardbook',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
          const SizedBox(height: 6),
          const Text(
            'Reporta problemas de acceso, sincronizacion, tarjetas, Book o alianzas desde la app.',
            style: TextStyle(color: AppColors.muted, height: 1.45),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => NativeActions.website(ApiConfig.publicBase),
                  icon: const Icon(Icons.public_rounded),
                  label: const Text('Web'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: FilledButton.icon(
                  onPressed: () => context.push('/support'),
                  icon: const Icon(Icons.support_agent_rounded),
                  label: const Text('Soporte'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _Avatar extends StatelessWidget {
  const _Avatar({required this.name, required this.avatarUrl});

  final String name;
  final String avatarUrl;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 86,
      height: 86,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: AppColors.panelSoft,
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: AppColors.stroke),
      ),
      child: avatarUrl.isEmpty
          ? Center(
              child: Text(_initials(name),
                  style: const TextStyle(
                      fontSize: 22, fontWeight: FontWeight.w900)))
          : Image.network(
              avatarUrl,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => Center(
                  child: Text(_initials(name),
                      style: const TextStyle(fontWeight: FontWeight.w900))),
            ),
    );
  }
}

class _InfoLine extends StatelessWidget {
  const _InfoLine({required this.icon, required this.value});

  final IconData icon;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: AppColors.muted, size: 18),
        const SizedBox(width: 8),
        Expanded(
            child: Text(value, style: const TextStyle(color: AppColors.muted))),
      ],
    );
  }
}

class _ProfileAction extends StatelessWidget {
  const _ProfileAction({
    required this.icon,
    required this.label,
    required this.onTap,
    this.color = AppColors.text,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(icon, color: color),
      title: Text(label,
          style: TextStyle(color: color, fontWeight: FontWeight.w800)),
      trailing: Icon(Icons.chevron_right_rounded,
          color: color.withValues(alpha: .72)),
      onTap: onTap,
    );
  }
}

String _fullName(Map<String, dynamic> profile) {
  final first = _text(profile['first_name']);
  final last = _text(profile['last_name']);
  final joined = [first, last].where((value) => value.isNotEmpty).join(' ');
  return joined.isEmpty
      ? _text(profile['username'], fallback: 'Cardbook')
      : joined;
}

String _text(dynamic value, {String fallback = ''}) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
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
