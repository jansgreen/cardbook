import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';

class AppMainMenu {
  const AppMainMenu._();

  static Future<void> show(BuildContext context) {
    return showModalBottomSheet<void>(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (sheetContext) => const _MainMenuSheet(),
    );
  }
}

class _MainMenuSheet extends StatelessWidget {
  const _MainMenuSheet();

  @override
  Widget build(BuildContext context) {
    final items = [
      _MenuItem(
          'Inicio', 'Resumen general de tu cuenta.', Icons.home_rounded, '/'),
      _MenuItem('Empresas', 'Administra empresas y conexiones.',
          Icons.business_center_rounded, '/companies'),
      _MenuItem('Tarjetas', 'Perfiles y tarjetas de presentacion.',
          Icons.qr_code_2_rounded, '/cards'),
      _MenuItem('Book', 'Tus empresas y contactos guardados.',
          Icons.bookmarks_rounded, '/book'),
      _MenuItem('Explorar', 'Empresas, talento y websites publicos.',
          Icons.travel_explore_rounded, '/marketplace'),
      _MenuItem('White Card Jobs', 'Perfiles laborales y candidatos.',
          Icons.work_outline_rounded, '/jobs'),
      _MenuItem('Alianzas', 'Solicitudes y conexiones empresariales.',
          Icons.handshake_rounded, '/alliances'),
      _MenuItem('Websites', 'Sitios creados con Website Builder.',
          Icons.public_rounded, '/websites'),
      _MenuItem('Notificaciones', 'Alianzas y actividad reciente.',
          Icons.notifications_rounded, '/notifications'),
      _MenuItem('Diagnostico', 'API, version, sesion y publicacion Android.',
          Icons.health_and_safety_rounded, '/diagnostics'),
      _MenuItem('Soporte', 'Reportes, ayuda y seguimiento de tickets.',
          Icons.support_agent_rounded, '/support'),
      _MenuItem('Perfil', 'Cuenta, version y cierre de sesion.',
          Icons.person_rounded, '/profile'),
    ];

    return SafeArea(
      top: false,
      child: Container(
        margin: const EdgeInsets.all(14),
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 18),
        decoration: BoxDecoration(
          color: AppColors.panel,
          borderRadius: BorderRadius.circular(AppRadius.lg),
          border: Border.all(color: AppColors.stroke),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: .42),
              blurRadius: 32,
              offset: const Offset(0, 18),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Expanded(
                  child: Text(
                    'Menu Cardbook',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
                  ),
                ),
                IconButton(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: const Icon(Icons.close_rounded),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Flexible(
              child: ListView.separated(
                shrinkWrap: true,
                itemCount: items.length,
                separatorBuilder: (_, __) => const SizedBox(height: 8),
                itemBuilder: (context, index) => _MenuTile(item: items[index]),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MenuItem {
  const _MenuItem(this.title, this.subtitle, this.icon, this.path);

  final String title;
  final String subtitle;
  final IconData icon;
  final String path;
}

class _MenuTile extends StatelessWidget {
  const _MenuTile({required this.item});

  final _MenuItem item;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () {
        Navigator.of(context).pop();
        context.go(item.path);
      },
      borderRadius: BorderRadius.circular(AppRadius.md),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.inkAlt.withValues(alpha: .68),
          borderRadius: BorderRadius.circular(AppRadius.md),
          border: Border.all(color: AppColors.stroke),
        ),
        child: Row(
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                color: AppColors.purple.withValues(alpha: .16),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Icon(item.icon, color: AppColors.purple),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(item.title,
                      style: const TextStyle(fontWeight: FontWeight.w900)),
                  const SizedBox(height: 3),
                  Text(
                    item.subtitle,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style:
                        const TextStyle(color: AppColors.muted, fontSize: 12),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right_rounded, color: AppColors.muted),
          ],
        ),
      ),
    );
  }
}
