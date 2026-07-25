import 'package:flutter/material.dart';
import 'package:mobile_cardbook/features/home/data/mobile_bootstrap_repository.dart';

class AppNavItem {
  const AppNavItem({
    required this.key,
    required this.label,
    required this.description,
    required this.icon,
    required this.path,
  });

  final String key;
  final String label;
  final String description;
  final IconData icon;
  final String path;
}

const _sectionRoutes = {
  'home': '/',
  'companies': '/companies',
  'cards': '/cards',
  'business_cards': '/cards',
  'book': '/book',
  'white_card_job': '/jobs',
  'notifications': '/notifications',
  'website': '/websites',
  'forms': '/forms',
  'ai_agents': '/ai-agents',
  'referrals': '/alliances',
  'public_site': '/marketplace',
};

const _sectionIcons = {
  'home': Icons.home_rounded,
  'companies': Icons.business_center_rounded,
  'cards': Icons.qr_code_2_rounded,
  'business_cards': Icons.badge_rounded,
  'book': Icons.bookmarks_rounded,
  'white_card_job': Icons.work_outline_rounded,
  'notifications': Icons.notifications_rounded,
  'website': Icons.public_rounded,
  'forms': Icons.dynamic_form_rounded,
  'ai_agents': Icons.smart_toy_rounded,
  'referrals': Icons.handshake_rounded,
  'public_site': Icons.travel_explore_rounded,
};

const _sectionDescriptions = {
  'home': 'Resumen general de tu cuenta.',
  'companies': 'Empresas, busqueda y conexiones.',
  'cards': 'Perfiles digitales del negocio.',
  'business_cards': 'Tarjetas de presentacion.',
  'book': 'Tu coleccion guardada.',
  'white_card_job': 'Perfil laboral y candidatos.',
  'notifications': 'Actividad reciente.',
  'website': 'Sitios creados con Website Builder.',
  'forms': 'Formularios conectados a tus websites.',
  'ai_agents': 'Asistentes, guias y leads con IA.',
  'referrals': 'Alianzas y referidos Cardbook.',
  'public_site': 'Explora servicios publicos.',
};

List<AppNavItem> appNavigationFromBootstrap(CardbookBootstrap bootstrap) {
  final items = <AppNavItem>[];
  for (final item in bootstrap.menu) {
    final path = _sectionRoutes[item.key];
    if (path == null) continue;
    if (items.any((existing) => existing.path == path)) continue;
    items.add(
      AppNavItem(
        key: item.key,
        label: _shortLabel(item),
        description: _sectionDescriptions[item.key] ?? 'Abrir ${item.label}.',
        icon: _sectionIcons[item.key] ?? Icons.apps_rounded,
        path: path,
      ),
    );
  }
  items.add(
    const AppNavItem(
      key: 'profile',
      label: 'Perfil',
      description: 'Cuenta, version y cierre de sesion.',
      icon: Icons.person_rounded,
      path: '/profile',
    ),
  );
  return items;
}

List<AppNavItem> bottomNavigationFromBootstrap(CardbookBootstrap bootstrap) {
  final all = appNavigationFromBootstrap(bootstrap);
  final priority = bootstrap.accountType == 'job'
      ? ['companies', 'white_card_job', 'book', 'notifications', 'profile']
      : ['home', 'companies', 'cards', 'book', 'profile'];
  final selected = <AppNavItem>[];
  for (final key in priority) {
    final match = _firstWhereOrNull(all, key);
    if (match != null) selected.add(match);
  }
  return selected.take(5).toList();
}

String defaultMobileRoute(CardbookBootstrap bootstrap) {
  final items = appNavigationFromBootstrap(bootstrap);
  if (bootstrap.accountType == 'job') {
    return items.any((item) => item.path == '/jobs') ? '/jobs' : '/book';
  }
  if (bootstrap.accountType == 'agent') {
    return items.any((item) => item.path == '/alliances') ? '/alliances' : '/';
  }
  return '/';
}

String _shortLabel(MobileMenuItem item) {
  if (item.key == 'white_card_job') return 'White Card';
  if (item.key == 'business_cards') return 'Presentacion';
  if (item.key == 'public_site') return 'Explorar';
  if (item.key == 'referrals') return 'Alianzas';
  return item.label;
}

AppNavItem? _firstWhereOrNull(List<AppNavItem> items, String key) {
  for (final item in items) {
    if (item.key == key) return item;
  }
  return null;
}
