import 'package:flutter/material.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';

class OfflineNotice extends StatelessWidget {
  const OfflineNotice({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: .12),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.gold.withValues(alpha: .35)),
      ),
      child: const Row(
        children: [
          Icon(Icons.wifi_off_rounded, color: AppColors.gold, size: 20),
          SizedBox(width: 10),
          Expanded(
            child: Text(
              'Mostrando datos guardados. Se actualizara cuando vuelva la conexion.',
              style: TextStyle(
                color: AppColors.text,
                fontWeight: FontWeight.w800,
                height: 1.35,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
