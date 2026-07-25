import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';

class PhysicalCardOcrResult {
  const PhysicalCardOcrResult({
    this.displayName = '',
    this.jobTitle = '',
    this.companyName = '',
    this.phone = '',
    this.email = '',
    this.website = '',
    this.address = '',
    this.services = '',
    this.rawText = '',
  });

  final String displayName;
  final String jobTitle;
  final String companyName;
  final String phone;
  final String email;
  final String website;
  final String address;
  final String services;
  final String rawText;

  int get filledCount {
    return [
      displayName,
      jobTitle,
      companyName,
      phone,
      email,
      website,
      address,
      services,
    ].where((value) => value.trim().isNotEmpty).length;
  }
}

class PhysicalCardOcr {
  const PhysicalCardOcr._();

  static Future<PhysicalCardOcrResult> extract(String imagePath) async {
    final recognizer = TextRecognizer(script: TextRecognitionScript.latin);
    try {
      final recognized =
          await recognizer.processImage(InputImage.fromFilePath(imagePath));
      final lines = recognized.blocks
          .expand((block) => block.lines)
          .map((line) => _clean(line.text))
          .where((line) => line.isNotEmpty)
          .toList();
      return _parse(lines, recognized.text);
    } finally {
      await recognizer.close();
    }
  }

  static PhysicalCardOcrResult _parse(List<String> lines, String rawText) {
    final email = _firstMatch(lines, RegExp(r'[\w.+-]+@[\w-]+\.[\w.-]+'));
    final website = _firstMatch(
      lines,
      RegExp(r'((https?:\/\/)?(www\.)?[\w-]+\.[a-zA-Z]{2,}[\w\/?.=&%-]*)'),
      reject: (value) => value.contains('@'),
    );
    final phone = _firstMatch(
      lines,
      RegExp(r'(\+?\d[\d\s().-]{7,}\d)'),
      reject: (value) => value.contains('.') && !value.contains('-'),
    );
    final company = _findCompany(lines);
    final title = _findTitle(lines);
    final name =
        _findName(lines, exclusions: {email, website, phone, company, title});
    final address = _findAddress(lines, exclusions: {email, website, phone});
    final services = _findServices(lines, exclusions: {
      email,
      website,
      phone,
      company,
      title,
      name,
      address,
    });

    return PhysicalCardOcrResult(
      displayName: name,
      jobTitle: title,
      companyName: company,
      phone: phone,
      email: email,
      website: website,
      address: address,
      services: services,
      rawText: rawText,
    );
  }

  static String _findCompany(List<String> lines) {
    final marker = RegExp(
      r'\b(llc|inc|corp|co\.?|company|technologies|solutions|group|studio|services)\b',
      caseSensitive: false,
    );
    for (final line in lines) {
      if (marker.hasMatch(line) && !_looksLikeContact(line)) return line;
    }
    return '';
  }

  static String _findTitle(List<String> lines) {
    final marker = RegExp(
      r'\b(ceo|founder|owner|manager|director|president|developer|designer|engineer|consultant|sales|admin|plumber|electrician|welder|mechanic)\b',
      caseSensitive: false,
    );
    for (final line in lines) {
      if (marker.hasMatch(line) && !_looksLikeContact(line)) return line;
    }
    return '';
  }

  static String _findName(List<String> lines,
      {required Set<String> exclusions}) {
    for (final line in lines) {
      if (exclusions.contains(line)) continue;
      if (_looksLikeContact(line)) continue;
      final words = line.split(RegExp(r'\s+'));
      if (words.length >= 2 && words.length <= 4 && line.length <= 45) {
        return line;
      }
    }
    return '';
  }

  static String _findAddress(List<String> lines,
      {required Set<String> exclusions}) {
    final marker = RegExp(
      r'\b(st|street|ave|avenue|road|rd|blvd|suite|paterson|santo domingo|ny|nj|rd)\b|,\s*[A-Z]{2}\b',
      caseSensitive: false,
    );
    for (final line in lines) {
      if (exclusions.contains(line)) continue;
      if (marker.hasMatch(line) && !_looksLikeContact(line)) return line;
    }
    return '';
  }

  static String _findServices(List<String> lines,
      {required Set<String> exclusions}) {
    final candidates = lines.where((line) {
      if (exclusions.contains(line)) return false;
      if (_looksLikeContact(line)) return false;
      return line.length > 18;
    }).take(3);
    return candidates.join(', ');
  }

  static String _firstMatch(
    List<String> lines,
    RegExp pattern, {
    bool Function(String value)? reject,
  }) {
    for (final line in lines) {
      final match = pattern.firstMatch(line);
      final value = match?.group(0);
      if (value != null && value.trim().isNotEmpty) {
        final clean = _clean(value);
        if (reject != null && reject(clean)) continue;
        return clean;
      }
    }
    return '';
  }

  static bool _looksLikeContact(String line) {
    return line.contains('@') ||
        line.contains('://') ||
        RegExp(r'\+?\d[\d\s().-]{7,}\d').hasMatch(line);
  }

  static String _clean(String value) {
    return value.replaceAll(RegExp(r'\s+'), ' ').trim();
  }
}
