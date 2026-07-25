import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/companies/data/companies_repository.dart';
import 'package:mobile_cardbook/features/home/data/mobile_bootstrap_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/company_tile.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/section_header.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class CompaniesScreen extends ConsumerStatefulWidget {
  const CompaniesScreen({super.key});

  @override
  ConsumerState<CompaniesScreen> createState() => _CompaniesScreenState();
}

class _CompaniesScreenState extends ConsumerState<CompaniesScreen> {
  final _search = TextEditingController();

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final companies = ref.watch(companiesProvider);
    final recommended = ref.watch(recommendedCompaniesProvider);
    final bootstrap = ref.watch(mobileBootstrapProvider);
    final canCreateCompany =
        bootstrap.valueOrNull?.can('can_create_company') ?? false;

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(companiesProvider);
              ref.invalidate(recommendedCompaniesProvider);
              await Future.wait([
                ref.read(companiesProvider.future),
                ref.read(recommendedCompaniesProvider.future),
              ]);
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
              children: [
                const BrandHeader(),
                const SizedBox(height: 24),
                const _CompaniesHero(),
                const SizedBox(height: 18),
                _SearchBox(
                  controller: _search,
                  onChanged: (_) => setState(() {}),
                ),
                const SizedBox(height: 18),
                GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      SectionHeader(
                        title: 'Mis empresas',
                        actionLabel: canCreateCompany ? 'Nueva' : null,
                        onAction: canCreateCompany
                            ? () => context.push('/companies/form')
                            : null,
                      ),
                      const SizedBox(height: 12),
                      companies.when(
                        loading: () => const SizedBox(
                            height: 120, child: AsyncStateView.loading()),
                        error: (_, __) => AsyncStateView.error(
                          'No pudimos cargar tus empresas.',
                          actionLabel: 'Reintentar',
                          onAction: () => ref.invalidate(companiesProvider),
                        ),
                        data: (items) {
                          final filtered = _filterCompanies(items);
                          return filtered.isEmpty
                              ? AsyncStateView.empty(
                                  canCreateCompany
                                      ? 'Crea tu primera empresa para publicar perfiles, tarjetas, websites y alianzas.'
                                      : 'No tienes empresas propias. Puedes explorar recomendadas y guardar negocios en Book.',
                                  title: canCreateCompany
                                      ? 'Empieza con una empresa'
                                      : 'Sin empresas propias',
                                  icon: canCreateCompany
                                      ? Icons.add_business_rounded
                                      : Icons.travel_explore_rounded,
                                  actionLabel:
                                      canCreateCompany ? 'Crear empresa' : null,
                                  onAction: canCreateCompany
                                      ? () => context.push('/companies/form')
                                      : null,
                                )
                              : Column(
                                  children: [
                                    for (final company in filtered) ...[
                                      CompanyTile(
                                        name: company['name']?.toString() ??
                                            'Empresa',
                                        description: company['description']
                                                ?.toString() ??
                                            company['category']?.toString() ??
                                            'Empresa Cardbook',
                                        rating: _compactNumber(
                                            company['efficient_count']),
                                        logoUrl: company['logo']?.toString(),
                                        onTap: () => context.push(
                                            '/companies/detail',
                                            extra: company),
                                      ),
                                      const SizedBox(height: 10),
                                    ],
                                  ],
                                );
                        },
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SectionHeader(
                          title: 'Empresas sugeridas', actionLabel: 'Filtrar'),
                      const SizedBox(height: 12),
                      recommended.when(
                        loading: () => const SizedBox(
                            height: 120, child: AsyncStateView.loading()),
                        error: (_, __) => AsyncStateView.error(
                          'No pudimos cargar sugerencias.',
                          actionLabel: 'Reintentar',
                          onAction: () =>
                              ref.invalidate(recommendedCompaniesProvider),
                        ),
                        data: (items) {
                          final filtered = _filterCompanies(items);
                          return filtered.isEmpty
                              ? const AsyncStateView.empty(
                                  'Vuelve mas tarde para ver empresas sugeridas por afinidad.',
                                  title: 'Sin sugerencias por ahora',
                                  icon: Icons.travel_explore_rounded,
                                )
                              : Column(
                                  children: [
                                    for (final company
                                        in filtered.take(12)) ...[
                                      CompanyTile(
                                        name: company['name']?.toString() ??
                                            'Empresa',
                                        description:
                                            company['category']?.toString() ??
                                                'Empresa sugerida',
                                        rating: _compactNumber(
                                            company['efficient_count']),
                                        logoUrl: company['logo']?.toString(),
                                        onTap: () => context.push(
                                            '/companies/detail',
                                            extra: company),
                                      ),
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
      bottomNavigationBar: const AppBottomNav(currentIndex: 1),
    );
  }

  List<Map<String, dynamic>> _filterCompanies(
      List<Map<String, dynamic>> items) {
    final query = _search.text.trim().toLowerCase();
    if (query.isEmpty) return items;
    return items.where((company) {
      final haystack = [
        company['name'],
        company['description'],
        company['category'],
        company['services'],
        company['city'],
        company['region'],
      ].map((value) => value?.toString().toLowerCase() ?? '').join(' ');
      return haystack.contains(query);
    }).toList();
  }

  static String _compactNumber(dynamic value) {
    final number =
        value is num ? value : num.tryParse(value?.toString() ?? '') ?? 0;
    if (number >= 1000) return '${(number / 1000).toStringAsFixed(1)}k';
    return number.toInt().toString();
  }
}

class _SearchBox extends StatelessWidget {
  const _SearchBox({
    required this.controller,
    required this.onChanged,
  });

  final TextEditingController controller;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      onChanged: onChanged,
      decoration: InputDecoration(
        hintText: 'Buscar por nombre, categoria, ciudad o servicio',
        prefixIcon: const Icon(Icons.search_rounded),
        suffixIcon: controller.text.trim().isEmpty
            ? const Icon(Icons.filter_list_rounded)
            : IconButton(
                onPressed: () {
                  controller.clear();
                  onChanged('');
                },
                icon: const Icon(Icons.close_rounded),
              ),
      ),
    );
  }
}

class _CompaniesHero extends StatelessWidget {
  const _CompaniesHero();

  @override
  Widget build(BuildContext context) {
    return const GlassCard(
      gradient: AppGradients.cardGlow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          StatusBadge(
              label: 'Red empresarial',
              icon: Icons.business_center_rounded,
              color: AppColors.gold),
          SizedBox(height: 16),
          Text('Empresas',
              style: TextStyle(
                  fontSize: 32, height: 1.05, fontWeight: FontWeight.w900)),
          SizedBox(height: 8),
          Text(
            'Administra tu presencia empresarial y descubre negocios con afinidad.',
            style: TextStyle(color: AppColors.muted, height: 1.45),
          ),
        ],
      ),
    );
  }
}
