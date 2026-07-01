import 'package:flutter/material.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';

class PostPreviewCard extends StatelessWidget {
  const PostPreviewCard({
    required this.companyName,
    required this.title,
    required this.caption,
    this.imageUrl,
    super.key,
  });

  final String companyName;
  final String title;
  final String caption;
  final String? imageUrl;

  @override
  Widget build(BuildContext context) {
    final url = imageUrl?.trim();
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.inkAlt.withOpacity(.72),
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(color: AppColors.stroke),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: AppGradients.primary,
                  border: Border.all(color: Colors.white.withOpacity(.16)),
                ),
                child: const Icon(Icons.business, size: 18),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(companyName, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w900)),
                    const Text('Hace poco', style: TextStyle(color: AppColors.muted, fontSize: 12)),
                  ],
                ),
              ),
              const Icon(Icons.more_horiz, color: AppColors.muted),
            ],
          ),
          const SizedBox(height: 12),
          Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
          if (caption.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(caption, maxLines: 3, overflow: TextOverflow.ellipsis, style: const TextStyle(color: AppColors.muted)),
          ],
          if (url != null && url.isNotEmpty) ...[
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(AppRadius.md),
              child: AspectRatio(
                aspectRatio: 16 / 9,
                child: Image.network(
                  url,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => const _PostImageFallback(),
                ),
              ),
            ),
          ],
          const SizedBox(height: 12),
          const Row(
            children: [
              Icon(Icons.thumb_up_alt_rounded, color: AppColors.blue, size: 18),
              SizedBox(width: 6),
              Text('Excelente', style: TextStyle(fontWeight: FontWeight.w800)),
            ],
          ),
        ],
      ),
    );
  }
}

class _PostImageFallback extends StatelessWidget {
  const _PostImageFallback();

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(gradient: AppGradients.cardGlow),
      child: const Center(
        child: Icon(Icons.image_outlined, color: AppColors.muted, size: 34),
      ),
    );
  }
}
