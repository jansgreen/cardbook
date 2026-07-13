import 'package:flutter/material.dart';
import 'package:mobile_cardbook/core/platform/nfc_actions.dart';
import 'package:mobile_cardbook/core/platform/native_actions.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:qr_flutter/qr_flutter.dart';

enum ShareTargetType {
  company,
  digitalCard,
  businessCard,
  whiteCardJob,
  website,
}

class SharePayload {
  const SharePayload({
    required this.type,
    required this.title,
    required this.url,
    this.subtitle = '',
    this.phone = '',
    this.email = '',
    this.website = '',
    this.address = '',
    this.organization = '',
    this.jobTitle = '',
  });

  final ShareTargetType type;
  final String title;
  final String subtitle;
  final String url;
  final String phone;
  final String email;
  final String website;
  final String address;
  final String organization;
  final String jobTitle;

  String get typeLabel {
    switch (type) {
      case ShareTargetType.company:
        return 'empresa';
      case ShareTargetType.digitalCard:
        return 'perfil de negocio';
      case ShareTargetType.businessCard:
        return 'tarjeta de presentacion';
      case ShareTargetType.whiteCardJob:
        return 'White Card Job';
      case ShareTargetType.website:
        return 'website';
    }
  }

  String get message {
    final lines = [
      title.trim(),
      if (subtitle.trim().isNotEmpty) subtitle.trim(),
      'Te comparto mi $typeLabel en Cardbook:',
      url.trim(),
    ];
    return lines.where((line) => line.isNotEmpty).join('\n');
  }
}

class ShareCenter {
  const ShareCenter._();

  static Future<void> show(BuildContext context, SharePayload payload) {
    if (payload.url.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('Este elemento todavia no tiene enlace publico.')),
      );
      return Future.value();
    }

    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _ShareCenterSheet(payload: payload),
    );
  }
}

class _ShareCenterSheet extends StatelessWidget {
  const _ShareCenterSheet({required this.payload});

  final SharePayload payload;

  @override
  Widget build(BuildContext context) {
    final actions = [
      _ShareAction(
        title: 'Compartir',
        subtitle: 'Abre Quick Share y apps instaladas',
        icon: Icons.ios_share_rounded,
        color: AppColors.purple,
        onTap: () => NativeActions.shareText(payload.title, payload.message),
      ),
      _ShareAction(
        title: 'WhatsApp',
        subtitle: 'Enviar por WhatsApp',
        icon: Icons.chat_rounded,
        color: AppColors.green,
        onTap: () =>
            NativeActions.whatsappMessage(payload.phone, payload.message),
      ),
      _ShareAction(
        title: 'Email',
        subtitle: 'Enviar por correo',
        icon: Icons.email_rounded,
        color: AppColors.blue,
        onTap: () => NativeActions.email(payload.email,
            subject: payload.title, body: payload.message),
      ),
      _ShareAction(
        title: 'SMS',
        subtitle: 'Enviar por mensaje',
        icon: Icons.sms_rounded,
        color: AppColors.cyan,
        onTap: () => NativeActions.sms(payload.phone, payload.message),
      ),
      _ShareAction(
        title: 'Copiar enlace',
        subtitle: 'Guardar link en portapapeles',
        icon: Icons.copy_rounded,
        color: AppColors.gold,
        onTap: () async {
          await NativeActions.copyText(payload.url);
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Enlace copiado.')),
            );
          }
        },
      ),
      _ShareAction(
        title: 'Ver QR',
        subtitle: 'Mostrar para escaneo rapido',
        icon: Icons.qr_code_2_rounded,
        color: AppColors.text,
        onTap: () async => _showQr(context, payload),
      ),
      _ShareAction(
        title: 'Contacto',
        subtitle: 'Compartir archivo .vcf',
        icon: Icons.contact_page_rounded,
        color: AppColors.green,
        onTap: () => NativeActions.shareContactCard(
          name: payload.title,
          organization: payload.organization,
          jobTitle: payload.jobTitle,
          phone: payload.phone,
          email: payload.email,
          website: payload.website.isNotEmpty ? payload.website : payload.url,
          address: payload.address,
          note: payload.subtitle,
        ),
      ),
      _ShareAction(
        title: 'Abrir publico',
        subtitle: 'Ver la pagina compartida',
        icon: Icons.open_in_new_rounded,
        color: AppColors.violet,
        onTap: () => NativeActions.website(payload.url),
      ),
      _ShareAction(
        title: 'NFC',
        subtitle: 'Grabar enlace en tag NFC',
        icon: Icons.nfc_rounded,
        color: AppColors.muted,
        onTap: () => _writeNfc(context, payload),
      ),
    ];

    return SafeArea(
      top: false,
      child: Container(
        margin: const EdgeInsets.all(14),
        padding: const EdgeInsets.fromLTRB(18, 16, 18, 18),
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
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(payload.title,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                              fontSize: 20, fontWeight: FontWeight.w900)),
                      const SizedBox(height: 4),
                      Text('Compartir ${payload.typeLabel}',
                          style: const TextStyle(
                              color: AppColors.muted, fontSize: 12)),
                    ],
                  ),
                ),
                IconButton(
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.close_rounded)),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.inkAlt.withValues(alpha: .7),
                borderRadius: BorderRadius.circular(AppRadius.md),
                border: Border.all(color: AppColors.stroke),
              ),
              child: Text(payload.url,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                      color: AppColors.purple, fontWeight: FontWeight.w800)),
            ),
            const SizedBox(height: 14),
            Flexible(
              child: GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                mainAxisSpacing: 10,
                crossAxisSpacing: 10,
                childAspectRatio: 2.45,
                children: [
                  for (final action in actions) _ShareActionTile(action: action)
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showQr(BuildContext context, SharePayload payload) {
    showDialog<void>(
      context: context,
      builder: (dialogContext) => Dialog(
        backgroundColor: AppColors.panel,
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppRadius.lg)),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(payload.title,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                      fontSize: 18, fontWeight: FontWeight.w900)),
              const SizedBox(height: 14),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(18)),
                child: QrImageView(
                  data: payload.url,
                  size: 220,
                  backgroundColor: Colors.white,
                  eyeStyle: const QrEyeStyle(
                      eyeShape: QrEyeShape.square, color: AppColors.ink),
                  dataModuleStyle: const QrDataModuleStyle(
                      dataModuleShape: QrDataModuleShape.circle,
                      color: AppColors.ink),
                ),
              ),
              const SizedBox(height: 14),
              Text(payload.url,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppColors.muted, fontSize: 12)),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => NativeActions.shareText(
                          payload.title, payload.message),
                      icon: const Icon(Icons.ios_share_rounded),
                      label: const Text('Compartir'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: FilledButton(
                      onPressed: () => Navigator.of(dialogContext).pop(),
                      child: const Text('Cerrar'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _writeNfc(BuildContext context, SharePayload payload) async {
    showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: AppColors.panel,
        title: const Row(
          children: [
            Icon(Icons.nfc_rounded, color: AppColors.purple),
            SizedBox(width: 10),
            Expanded(child: Text('Escribir NFC')),
          ],
        ),
        content: const Text(
          'Acerca una etiqueta NFC al telefono. Cardbook guardara el enlace publico para que pueda abrirse al tocarla.',
          style: TextStyle(color: AppColors.muted, height: 1.45),
        ),
        actions: [
          TextButton(
            onPressed: () async {
              await NfcActions.stopSession();
              if (dialogContext.mounted) Navigator.of(dialogContext).pop();
            },
            child: const Text('Cancelar'),
          ),
        ],
      ),
    );

    final result = await NfcActions.writeUrlToTag(payload.url);
    if (!context.mounted) return;
    final navigator = Navigator.of(context, rootNavigator: true);
    if (navigator.canPop()) navigator.pop();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(_nfcMessage(result))),
    );
  }

  String _nfcMessage(NfcWriteResult result) {
    switch (result) {
      case NfcWriteResult.written:
        return 'Enlace Cardbook guardado en NFC.';
      case NfcWriteResult.unsupported:
        return 'Este dispositivo no soporta NFC.';
      case NfcWriteResult.disabled:
        return 'NFC esta desactivado en este dispositivo.';
      case NfcWriteResult.notWritable:
        return 'Esta etiqueta NFC no se puede escribir.';
      case NfcWriteResult.tooSmall:
        return 'La etiqueta NFC no tiene espacio suficiente.';
      case NfcWriteResult.failed:
        return 'No pudimos escribir el enlace NFC.';
    }
  }
}

class _ShareAction {
  const _ShareAction({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final Color color;
  final Future<void> Function() onTap;
}

class _ShareActionTile extends StatelessWidget {
  const _ShareActionTile({required this.action});

  final _ShareAction action;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () async {
        await action.onTap();
      },
      borderRadius: BorderRadius.circular(AppRadius.md),
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: AppColors.inkAlt.withValues(alpha: .76),
          borderRadius: BorderRadius.circular(AppRadius.md),
          border: Border.all(color: AppColors.stroke),
        ),
        child: Row(
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                color: action.color.withValues(alpha: .16),
                borderRadius: BorderRadius.circular(13),
              ),
              child: Icon(action.icon, color: action.color, size: 20),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(action.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                          fontWeight: FontWeight.w900, fontSize: 13)),
                  const SizedBox(height: 2),
                  Text(action.subtitle,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                          color: AppColors.muted, fontSize: 10)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
