import 'dart:io';

import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';

class NativeActions {
  const NativeActions._();

  static Future<void> call(String? phone) async {
    final value = _clean(phone);
    if (value.isEmpty) return;
    await _open(Uri(scheme: 'tel', path: value));
  }

  static Future<void> email(String? address,
      {String? subject, String? body}) async {
    final value = _clean(address);
    await _open(Uri(
      scheme: 'mailto',
      path: value,
      queryParameters: {
        'subject': subject ?? 'Cardbook',
        if (_clean(body).isNotEmpty) 'body': _clean(body),
      },
    ));
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

  static Future<void> whatsappMessage(
      String? phoneOrUrl, String message) async {
    final raw = _clean(phoneOrUrl);
    final encoded = Uri.encodeComponent(_clean(message));
    if (raw.startsWith('http')) {
      await _open(
          Uri.parse('$raw${raw.contains('?') ? '&' : '?'}text=$encoded'));
      return;
    }
    final digits = raw.replaceAll(RegExp(r'[^0-9+]'), '');
    final url = digits.isEmpty
        ? 'https://wa.me/?text=$encoded'
        : 'https://wa.me/$digits?text=$encoded';
    await _open(Uri.parse(url));
  }

  static Future<void> sms(String? phone, String message) async {
    final value = _clean(phone);
    final uri = Uri(
      scheme: 'sms',
      path: value,
      queryParameters: {'body': _clean(message)},
    );
    await _open(uri);
  }

  static Future<void> maps(String? address) async {
    final value = _clean(address);
    if (value.isEmpty) return;
    await _open(Uri.parse(
        'https://www.google.com/maps/search/?api=1&query=${Uri.encodeComponent(value)}'));
  }

  static Future<void> shareText(String title, String text) async {
    final cleanTitle = _clean(title);
    final cleanText = _clean(text);
    if (cleanText.isEmpty) return;
    await Share.share(cleanText,
        subject: cleanTitle.isEmpty ? 'Cardbook' : cleanTitle);
  }

  static Future<void> shareContactCard({
    required String name,
    String organization = '',
    String jobTitle = '',
    String phone = '',
    String email = '',
    String website = '',
    String address = '',
    String note = '',
  }) async {
    final cleanName = _clean(name);
    if (cleanName.isEmpty) return;

    final directory = await getTemporaryDirectory();
    final fileName = '${_fileSafe(cleanName)}.vcf';
    final file = File('${directory.path}${Platform.pathSeparator}$fileName');
    await file.writeAsString(
      _buildVCard(
        name: cleanName,
        organization: organization,
        jobTitle: jobTitle,
        phone: phone,
        email: email,
        website: website,
        address: address,
        note: note,
      ),
      flush: true,
    );

    await Share.shareXFiles(
      [XFile(file.path, mimeType: 'text/vcard', name: fileName)],
      subject: cleanName,
      text: 'Contacto de $cleanName en Cardbook',
    );
  }

  static Future<void> copyText(String text) async {
    final value = _clean(text);
    if (value.isEmpty) return;
    await Clipboard.setData(ClipboardData(text: value));
  }

  static Future<void> _open(Uri uri) async {
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      await launchUrl(uri, mode: LaunchMode.platformDefault);
    }
  }

  static String _clean(String? value) => value?.trim() ?? '';

  static String _buildVCard({
    required String name,
    required String organization,
    required String jobTitle,
    required String phone,
    required String email,
    required String website,
    required String address,
    required String note,
  }) {
    final lines = <String>[
      'BEGIN:VCARD',
      'VERSION:3.0',
      'FN:${_vCardEscape(name)}',
      if (_clean(organization).isNotEmpty) 'ORG:${_vCardEscape(organization)}',
      if (_clean(jobTitle).isNotEmpty) 'TITLE:${_vCardEscape(jobTitle)}',
      if (_clean(phone).isNotEmpty) 'TEL;TYPE=CELL:${_vCardEscape(phone)}',
      if (_clean(email).isNotEmpty) 'EMAIL:${_vCardEscape(email)}',
      if (_clean(website).isNotEmpty) 'URL:${_vCardEscape(website)}',
      if (_clean(address).isNotEmpty)
        'ADR;TYPE=WORK:;;${_vCardEscape(address)}',
      if (_clean(note).isNotEmpty) 'NOTE:${_vCardEscape(note)}',
      'END:VCARD',
    ];
    return '${lines.join('\r\n')}\r\n';
  }

  static String _vCardEscape(String value) {
    return _clean(value)
        .replaceAll(r'\', r'\\')
        .replaceAll(';', r'\;')
        .replaceAll(',', r'\,')
        .replaceAll('\r\n', r'\n')
        .replaceAll('\n', r'\n');
  }

  static String _fileSafe(String value) {
    final normalized = _clean(value)
        .replaceAll(RegExp(r'[^a-zA-Z0-9_-]+'), '_')
        .replaceAll(RegExp(r'_+'), '_')
        .replaceAll(RegExp(r'^_|_$'), '');
    return normalized.isEmpty ? 'cardbook_contact' : normalized;
  }
}
