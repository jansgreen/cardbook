import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
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
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
            children: [
              const BrandHeader(),
              const SizedBox(height: 24),
              profile.when(
                loading: () => const SizedBox(height: 220, child: AsyncStateView.loading()),
                error: (_, __) => const AsyncStateView.error('No pudimos cargar tu perfil.'),
                data: (data) => _ProfileContent(profile: data),
              ),
            ],
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
    final language = _text(profile['preferred_language'], fallback: 'es').toUpperCase();
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
              StatusBadge(label: 'Cuenta Cardbook', icon: Icons.verified_user_rounded, color: AppColors.gold),
              const SizedBox(height: 16),
              Text(fullName, style: const TextStyle(fontSize: 30, height: 1.05, fontWeight: FontWeight.w900)),
              const SizedBox(height: 6),
              Text('@$username', style: const TextStyle(color: AppColors.purple, fontWeight: FontWeight.w800)),
              if (email.isNotEmpty) ...[
                const SizedBox(height: 12),
                _InfoLine(icon: Icons.email_rounded, value: email),
              ],
              if (phone.isNotEmpty) ...[
                const SizedBox(height: 8),
                _InfoLine(icon: Icons.call_rounded, value: phone),
              ],
              const SizedBox(height: 8),
              _InfoLine(icon: Icons.translate_rounded, value: 'Idioma $language'),
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
                icon: Icons.public_rounded,
                label: 'Sitio publico',
                onTap: () => context.go('/'),
              ),
              _ProfileAction(
                icon: Icons.logout_rounded,
                label: 'Cerrar sesion',
                color: AppColors.red,
                onTap: () => _logout(context, ref),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Future<void> _logout(BuildContext context, WidgetRef ref) async {
    await ref.read(authRepositoryProvider).logout();
    ref.invalidate(profileProvider);
    if (context.mounted) context.go('/login');
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
          ? Center(child: Text(_initials(name), style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900)))
          : Image.network(
              avatarUrl,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => Center(child: Text(_initials(name), style: const TextStyle(fontWeight: FontWeight.w900))),
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
        Expanded(child: Text(value, style: const TextStyle(color: AppColors.muted))),
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
      title: Text(label, style: TextStyle(color: color, fontWeight: FontWeight.w800)),
      trailing: Icon(Icons.chevron_right_rounded, color: color.withOpacity(.72)),
      onTap: onTap,
    );
  }
}

String _fullName(Map<String, dynamic> profile) {
  final first = _text(profile['first_name']);
  final last = _text(profile['last_name']);
  final joined = [first, last].where((value) => value.isNotEmpty).join(' ');
  return joined.isEmpty ? _text(profile['username'], fallback: 'Cardbook') : joined;
}

String _text(dynamic value, {String fallback = ''}) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
}

String _initials(String value) {
  final words = value.trim().split(RegExp(r'\s+')).where((word) => word.isNotEmpty).toList();
  if (words.isEmpty) return 'CB';
  if (words.length == 1) return words.first.substring(0, words.first.length >= 2 ? 2 : 1).toUpperCase();
  return '${words[0][0]}${words[1][0]}'.toUpperCase();
}
