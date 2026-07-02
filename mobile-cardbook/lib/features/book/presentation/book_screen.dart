import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/book/data/book_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/company_tile.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/section_header.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class BookScreen extends ConsumerWidget {
  const BookScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final book = ref.watch(bookProvider);

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
            children: [
              const BrandHeader(),
              const SizedBox(height: 24),
              const _BookHero(),
              const SizedBox(height: 18),
              GlassCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SectionHeader(title: 'Guardados', actionLabel: 'Ordenar'),
                    const SizedBox(height: 12),
                    book.when(
                      loading: () => const SizedBox(height: 120, child: AsyncStateView.loading()),
                      error: (_, __) => const AsyncStateView.error('No pudimos cargar tu Book.'),
                      data: (items) => items.isEmpty
                          ? const AsyncStateView.empty('Cuando guardes tarjetas o perfiles, apareceran aqui.')
                          : Column(
                              children: [
                                for (final item in items) ...[
                                  _BookTile(item: item),
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
      bottomNavigationBar: const AppBottomNav(currentIndex: 3),
    );
  }
}

class _BookTile extends ConsumerWidget {
  const _BookTile({required this.item});

  final Map<String, dynamic> item;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final company = item['company_detail'] is Map<String, dynamic> ? item['company_detail'] as Map<String, dynamic> : <String, dynamic>{};
    final notes = item['notes']?.toString().trim() ?? '';
    return Column(
      children: [
        CompanyTile(
          name: company['name']?.toString() ?? 'Negocio guardado',
          description: notes.isNotEmpty ? notes : company['description']?.toString() ?? 'Guardado en Book',
          rating: _compactNumber(company['efficient_count']),
          logoUrl: company['logo']?.toString(),
          onTap: () => context.push('/companies/detail', extra: company),
        ),
        const SizedBox(height: 8),
        Align(
          alignment: Alignment.centerRight,
          child: TextButton.icon(
            onPressed: () => _remove(context, ref),
            icon: const Icon(Icons.delete_outline_rounded, size: 18, color: AppColors.red),
            label: const Text('Quitar de Book', style: TextStyle(color: AppColors.red)),
          ),
        ),
      ],
    );
  }

  Future<void> _remove(BuildContext context, WidgetRef ref) async {
    final id = item['id'];
    if (id is! int) return;
    try {
      await ref.read(bookRepositoryProvider).remove(id);
      ref.invalidate(bookProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Quitado de Book.')),
        );
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No pudimos quitar este guardado.')),
        );
      }
    }
  }

  static String _compactNumber(dynamic value) {
    final number = value is num ? value : num.tryParse(value?.toString() ?? '') ?? 0;
    if (number >= 1000) return '${(number / 1000).toStringAsFixed(1)}k';
    return number.toInt().toString();
  }
}

class _BookHero extends StatelessWidget {
  const _BookHero();

  @override
  Widget build(BuildContext context) {
    return const GlassCard(
      gradient: AppGradients.cardGlow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          StatusBadge(label: 'Coleccion empresarial', icon: Icons.bookmarks_rounded, color: AppColors.gold),
          SizedBox(height: 16),
          Text('Book', style: TextStyle(fontSize: 32, height: 1.05, fontWeight: FontWeight.w900)),
          SizedBox(height: 8),
          Text(
            'Tus empresas, tarjetas y perfiles guardados en un solo lugar.',
            style: TextStyle(color: AppColors.muted, height: 1.45),
          ),
        ],
      ),
    );
  }
}
