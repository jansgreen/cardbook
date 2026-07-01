import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/companies/data/companies_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/company_tile.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/section_header.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class CompaniesScreen extends ConsumerWidget {
  const CompaniesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final companies = ref.watch(companiesProvider);
    final recommended = ref.watch(recommendedCompaniesProvider);

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
            children: [
              const BrandHeader(),
              const SizedBox(height: 24),
              const _CompaniesHero(),
              const SizedBox(height: 18),
              GlassCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SectionHeader(
                      title: 'Mis empresas',
                      actionLabel: 'Nueva',
                      onAction: () => context.push('/companies/form'),
                    ),
                    const SizedBox(height: 12),
                    companies.when(
                      loading: () => const SizedBox(height: 120, child: AsyncStateView.loading()),
                      error: (_, __) => const AsyncStateView.error('No pudimos cargar tus empresas.'),
                      data: (items) => items.isEmpty
                          ? const AsyncStateView.empty('Aun no tienes empresas creadas.')
                          : Column(
                              children: [
                                for (final company in items) ...[
                                  CompanyTile(
                                    name: company['name']?.toString() ?? 'Empresa',
                                    description: company['description']?.toString() ?? company['category']?.toString() ?? 'Empresa Cardbook',
                                    rating: _compactNumber(company['efficient_count']),
                                    logoUrl: company['logo']?.toString(),
                                    onTap: () => context.push('/companies/detail', extra: company),
                                  ),
                                  const SizedBox(height: 10),
                                ],
                              ],
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
                    const SectionHeader(title: 'Empresas sugeridas', actionLabel: 'Filtrar'),
                    const SizedBox(height: 12),
                    recommended.when(
                      loading: () => const SizedBox(height: 120, child: AsyncStateView.loading()),
                      error: (_, __) => const AsyncStateView.error('No pudimos cargar sugerencias.'),
                      data: (items) => items.isEmpty
                          ? const AsyncStateView.empty('No hay sugerencias disponibles por ahora.')
                          : Column(
                              children: [
                                for (final company in items.take(6)) ...[
                                  CompanyTile(
                                    name: company['name']?.toString() ?? 'Empresa',
                                    description: company['category']?.toString() ?? 'Empresa sugerida',
                                    rating: _compactNumber(company['efficient_count']),
                                    logoUrl: company['logo']?.toString(),
                                    onTap: () => context.push('/companies/detail', extra: company),
                                  ),
                                  const SizedBox(height: 10),
                                ],
                              ],
                            ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: 1),
    );
  }

  static String _compactNumber(dynamic value) {
    final number = value is num ? value : num.tryParse(value?.toString() ?? '') ?? 0;
    if (number >= 1000) return '${(number / 1000).toStringAsFixed(1)}k';
    return number.toInt().toString();
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
          StatusBadge(label: 'Red empresarial', icon: Icons.business_center_rounded, color: AppColors.gold),
          SizedBox(height: 16),
          Text('Empresas', style: TextStyle(fontSize: 32, height: 1.05, fontWeight: FontWeight.w900)),
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
