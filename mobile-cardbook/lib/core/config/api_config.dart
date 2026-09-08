class ApiConfig {
  static const baseUrl = String.fromEnvironment(
    'CARDBOOK_API_BASE_URL',
    defaultValue: 'https://incardbook.com',
  );

  static String get apiBase =>
      '${baseUrl.replaceAll(RegExp(r'/$'), '')}/api/v1';
  static String get publicBase => baseUrl.replaceAll(RegExp(r'/$'), '');
}
