import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';

class AppBottomNav extends StatelessWidget {
  const AppBottomNav({required this.currentIndex, super.key});

  final int? currentIndex;

  @override
  Widget build(BuildContext context) {
    final items = [
      _NavItem('Inicio', Icons.home_outlined, '/'),
      _NavItem('Empresas', Icons.business_center_outlined, '/companies'),
      _NavItem('Tarjetas', Icons.qr_code_2_outlined, '/cards'),
      _NavItem('Book', Icons.bookmarks_outlined, '/book'),
      _NavItem('Perfil', Icons.person_outline, '/profile'),
    ];

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
                selected: i == currentIndex,
                isPrimary: false,
                onTap: () => context.go(items[i].path),
              ),
          ],
        ),
      ),
    );
  }
}

class _NavItem {
  const _NavItem(this.label, this.icon, this.path);
  final String label;
  final IconData icon;
  final String path;
}

class _BottomNavButton extends StatelessWidget {
  const _BottomNavButton({
    required this.item,
    required this.selected,
    required this.isPrimary,
    required this.onTap,
  });

  final _NavItem item;
  final bool selected;
  final bool isPrimary;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    if (isPrimary) {
      return GestureDetector(
        onTap: onTap,
        child: Container(
          width: 54,
          height: 54,
          decoration: const BoxDecoration(
            shape: BoxShape.circle,
            gradient: AppGradients.primary,
            boxShadow: [
              BoxShadow(
                color: Color(0x663B36FF),
                blurRadius: 18,
                offset: Offset(0, 8),
              ),
            ],
          ),
          child: Icon(item.icon, color: Colors.white),
        ),
      );
    }
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
