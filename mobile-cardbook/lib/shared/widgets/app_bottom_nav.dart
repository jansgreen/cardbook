import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/home/data/mobile_bootstrap_repository.dart';
import 'package:mobile_cardbook/shared/navigation/mobile_navigation.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';

class AppBottomNav extends ConsumerWidget {
  const AppBottomNav({required this.currentIndex, super.key});

  final int? currentIndex;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bootstrap = ref.watch(mobileBootstrapProvider);
    final items = bootstrap.maybeWhen(
      data: bottomNavigationFromBootstrap,
      orElse: () => const [
        AppNavItem(
          key: 'home',
          label: 'Inicio',
          description: 'Resumen general.',
          icon: Icons.home_rounded,
          path: '/',
        ),
        AppNavItem(
          key: 'profile',
          label: 'Perfil',
          description: 'Cuenta.',
          icon: Icons.person_rounded,
          path: '/profile',
        ),
      ],
    );
    final currentPath = GoRouterState.of(context).uri.path;

    return SafeArea(
      top: false,
      child: Container(
        margin: const EdgeInsets.fromLTRB(18, 0, 18, 12),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: AppColors.panel.withValues(alpha: .96),
          borderRadius: BorderRadius.circular(AppRadius.lg),
          border: Border.all(color: AppColors.stroke.withValues(alpha: .9)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: .34),
              blurRadius: 28,
              offset: const Offset(0, 16),
            ),
          ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            for (int i = 0; i < items.length; i++)
              _BottomNavButton(
                item: items[i],
                selected: itemIsSelected(items[i], currentPath, i),
                onTap: () => context.go(items[i].path),
              ),
          ],
        ),
      ),
    );
  }

  bool itemIsSelected(AppNavItem item, String currentPath, int index) {
    if (currentPath == item.path) return true;
    if (item.path != '/' && currentPath.startsWith(item.path)) return true;
    return currentIndex != null && index == currentIndex && currentPath == '/';
  }
}

class _BottomNavButton extends StatelessWidget {
  const _BottomNavButton({
    required this.item,
    required this.selected,
    required this.onTap,
  });

  final AppNavItem item;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: SizedBox(
        width: 64,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(item.icon,
                color: selected ? AppColors.purple : AppColors.text, size: 22),
            const SizedBox(height: 4),
            Text(
              item.label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                color: selected ? AppColors.purple : AppColors.text,
                fontSize: 10,
                fontWeight: selected ? FontWeight.w800 : FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
