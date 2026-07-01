import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/config/app_version.dart';
import 'package:mobile_cardbook/core/platform/native_actions.dart';
import 'package:mobile_cardbook/features/updates/data/app_update_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class UpdateStatusCard extends ConsumerWidget {
  const UpdateStatusCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final update = ref.watch(appUpdateProvider);

    return update.when(
      loading: () => const GlassCard(
        child: Row(
          children: [
            SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.purple)),
            SizedBox(width: 12),
            Expanded(child: Text('Buscando actualizaciones...', style: TextStyle(color: AppColors.muted))),
          ],
        ),
      ),
      error: (_, __) => GlassCard(
        child: Row(
          children: [
            const Icon(Icons.info_outline_rounded, color: AppColors.muted),
            const SizedBox(width: 12),
            const Expanded(child: Text('No pudimos consultar actualizaciones.', style: TextStyle(color: AppColors.muted))),
            IconButton(
              onPressed: () => ref.invalidate(appUpdateProvider),
              icon: const Icon(Icons.refresh_rounded),
            ),
          ],
        ),
      ),
      data: (info) => GlassCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            StatusBadge(
              label: info.hasUpdate ? 'Actualizacion disponible' : 'App actualizada',
              icon: info.hasUpdate ? Icons.system_update_alt_rounded : Icons.verified_rounded,
              color: info.hasUpdate ? AppColors.gold : AppColors.green,
            ),
            const SizedBox(height: 14),
            Text(
              info.hasUpdate ? info.message : 'Tienes la version mas reciente disponible.',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900),
            ),
            const SizedBox(height: 8),
            Text(
              'Instalada ${AppVersion.name} (${AppVersion.code}) - Disponible ${info.latestVersionName} (${info.latestVersionCode})',
              style: const TextStyle(color: AppColors.muted, height: 1.35),
            ),
            if (info.changelog.isNotEmpty) ...[
              const SizedBox(height: 12),
              for (final item in info.changelog.take(3))
                Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.check_circle_rounded, size: 16, color: AppColors.purple),
                      const SizedBox(width: 8),
                      Expanded(child: Text(item, style: const TextStyle(color: AppColors.muted))),
                    ],
                  ),
                ),
            ],
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => ref.invalidate(appUpdateProvider),
                    icon: const Icon(Icons.refresh_rounded),
                    label: const Text('Revisar'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: info.downloadUrl.isEmpty ? null : () => NativeActions.website(info.downloadUrl),
                    icon: const Icon(Icons.download_rounded),
                    label: const Text('Descargar'),
                  ),
                ),
              ],
            ),
            if (info.releasePageUrl.isNotEmpty) ...[
              const SizedBox(height: 8),
              TextButton.icon(
                onPressed: () => NativeActions.website(info.releasePageUrl),
                icon: const Icon(Icons.open_in_new_rounded),
                label: const Text('Ver pagina de descarga'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
