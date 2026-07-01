import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';

class NativeActions {
  const NativeActions._();

  static Future<void> call(String? phone) async {
    final value = _clean(phone);
    if (value.isEmpty) return;
    await _open(Uri(scheme: 'tel', path: value));
  }

  static Future<void> email(String? address, {String? subject}) async {
    final value = _clean(address);
    if (value.isEmpty) return;
    await _open(Uri(scheme: 'mailto', path: value, queryParameters: {'subject': subject ?? 'Cardbook'}));
  }

  static Future<void> website(String? url) async {
    final value = _clean(url);
    if (value.isEmpty) return;
    final uri = Uri.parse(value.startsWith('http') ? value : 'https://$value');
    await _open(uri);
  }

  static Future<void> whatsapp(String? value) async {
    final raw = _clean(value);
    if (raw.isEmpty) return;
    if (raw.startsWith('http')) {
      await _open(Uri.parse(raw));
      return;
    }
    final digits = raw.replaceAll(RegExp(r'[^0-9+]'), '');
    if (digits.isEmpty) return;
    await _open(Uri.parse('https://wa.me/$digits'));
  }

  static Future<void> maps(String? address) async {
    final value = _clean(address);
    if (value.isEmpty) return;
    await _open(Uri.parse('https://www.google.com/maps/search/?api=1&query=${Uri.encodeComponent(value)}'));
  }

  static Future<void> shareText(String title, String text) async {
    final cleanTitle = _clean(title);
    final cleanText = _clean(text);
    if (cleanText.isEmpty) return;
    await Share.share(cleanText, subject: cleanTitle.isEmpty ? 'Cardbook' : cleanTitle);
  }

  static Future<void> _open(Uri uri) async {
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      await launchUrl(uri, mode: LaunchMode.platformDefault);
    }
  }

  static String _clean(String? value) => value?.trim() ?? '';
}
