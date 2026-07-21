import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/config/api_config.dart';
import 'package:mobile_cardbook/core/config/app_version.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/storage/token_storage.dart';

final diagnosticsRepositoryProvider = Provider<DiagnosticsRepository>((ref) {
  return DiagnosticsRepository(
    apiClient: ref.read(apiClientProvider),
    tokenStorage: ref.read(tokenStorageProvider),
  );
});

final diagnosticsProvider = FutureProvider<DiagnosticsReport>((ref) async {
  return ref.read(diagnosticsRepositoryProvider).run();
});

class DiagnosticsRepository {
  const DiagnosticsRepository({
    required ApiClient apiClient,
    required TokenStorage tokenStorage,
  })  : _apiClient = apiClient,
        _tokenStorage = tokenStorage;

  final ApiClient _apiClient;
  final TokenStorage _tokenStorage;

  Future<DiagnosticsReport> run() async {
    final access = await _tokenStorage.readAccess();
    final refresh = await _tokenStorage.readRefresh();

    final checks = await Future.wait<DiagnosticCheck>([
      _checkPublicHealth(),
      _checkReadiness(),
      _checkMobileConfig(),
      _checkApiAuth(access),
      _checkMobileDashboard(access),
      _checkAndroidVersion(),
    ]);

    return DiagnosticsReport(
      generatedAt: DateTime.now(),
      appVersionName: AppVersion.name,
      appVersionCode: AppVersion.code,
      packageName: AppVersion.packageName,
      apiBaseUrl: ApiConfig.apiBase,
      publicBaseUrl: ApiConfig.publicBase,
      hasAccessToken: access != null && access.isNotEmpty,
      hasRefreshToken: refresh != null && refresh.isNotEmpty,
      checks: checks,
    );
  }

  Future<DiagnosticCheck> _checkPublicHealth() async {
    try {
      final response = await _apiClient.dio.get<Map<String, dynamic>>(
        '${ApiConfig.publicBase}/health/',
        options: Options(extra: {'diagnostic': true}),
      );
      final data = response.data ?? {};
      return DiagnosticCheck.ok(
        title: 'Health publico',
        target: '/health/',
        message: data['status']?.toString() ?? 'Servicio disponible',
        statusCode: response.statusCode,
      );
    } on DioException catch (error) {
      return DiagnosticCheck.fail(
        title: 'Health publico',
        target: '/health/',
        message: _errorMessage(error),
        statusCode: error.response?.statusCode,
      );
    }
  }

  Future<DiagnosticCheck> _checkReadiness() async {
    try {
      final response = await _apiClient.dio.get<Map<String, dynamic>>(
        '${ApiConfig.publicBase}/health/ready/',
        options: Options(extra: {'diagnostic': true}),
      );
      final data = response.data ?? {};
      return DiagnosticCheck.ok(
        title: 'Readiness produccion',
        target: '/health/ready/',
        message: data['status']?.toString() ?? 'Listo',
        statusCode: response.statusCode,
      );
    } on DioException catch (error) {
      final status = error.response?.statusCode;
      return DiagnosticCheck(
        title: 'Readiness produccion',
        target: '/health/ready/',
        message: _errorMessage(error),
        statusCode: status,
        state: status == 503 ? DiagnosticState.warning : DiagnosticState.fail,
      );
    }
  }

  Future<DiagnosticCheck> _checkApiAuth(String? access) async {
    if (access == null || access.isEmpty) {
      return const DiagnosticCheck(
        title: 'Sesion API',
        target: '/api/v1/accounts/me/',
        message:
            'No hay token local. Inicia sesion para probar endpoints privados.',
        state: DiagnosticState.warning,
      );
    }

    try {
      final response = await _apiClient.dio.get<Map<String, dynamic>>(
        '/accounts/me/',
        options: Options(extra: {'diagnostic': true}),
      );
      return DiagnosticCheck.ok(
        title: 'Sesion API',
        target: '/api/v1/accounts/me/',
        message: 'Token aceptado por la API',
        statusCode: response.statusCode,
      );
    } on DioException catch (error) {
      return DiagnosticCheck.fail(
        title: 'Sesion API',
        target: '/api/v1/accounts/me/',
        message: _errorMessage(error),
        statusCode: error.response?.statusCode,
      );
    }
  }

  Future<DiagnosticCheck> _checkMobileConfig() async {
    try {
      final response = await _apiClient.dio.get<Map<String, dynamic>>(
        '/mobile/config/',
        options: Options(extra: {'diagnostic': true}),
      );
      final data = response.data ?? {};
      final message = data['message']?.toString() ??
          data['status']?.toString() ??
          'Configuracion movil disponible';
      return DiagnosticCheck.ok(
        title: 'Config movil',
        target: '/api/v1/mobile/config/',
        message: message,
        statusCode: response.statusCode,
      );
    } on DioException catch (error) {
      return DiagnosticCheck.fail(
        title: 'Config movil',
        target: '/api/v1/mobile/config/',
        message: _errorMessage(error),
        statusCode: error.response?.statusCode,
      );
    }
  }

  Future<DiagnosticCheck> _checkMobileDashboard(String? access) async {
    if (access == null || access.isEmpty) {
      return const DiagnosticCheck(
        title: 'Dashboard movil',
        target: '/api/v1/mobile/dashboard/',
        message:
            'No hay token local. Inicia sesion para probar el resumen movil.',
        state: DiagnosticState.warning,
      );
    }

    try {
      final response = await _apiClient.dio.get<Map<String, dynamic>>(
        '/mobile/dashboard/',
        options: Options(extra: {'diagnostic': true}),
      );
      return DiagnosticCheck.ok(
        title: 'Dashboard movil',
        target: '/api/v1/mobile/dashboard/',
        message: 'Resumen movil disponible para la sesion actual',
        statusCode: response.statusCode,
      );
    } on DioException catch (error) {
      return DiagnosticCheck.fail(
        title: 'Dashboard movil',
        target: '/api/v1/mobile/dashboard/',
        message: _errorMessage(error),
        statusCode: error.response?.statusCode,
      );
    }
  }

  Future<DiagnosticCheck> _checkAndroidVersion() async {
    try {
      final response = await _apiClient.dio.get<Map<String, dynamic>>(
        '${ApiConfig.publicBase}/android/version/',
        options: Options(extra: {'diagnostic': true}),
      );
      final data = response.data ?? {};
      final latestCode = _intValue(data['latest_version_code']);
      final latestName = data['latest_version_name']?.toString() ?? '';
      final signing = data['signing']?.toString() ?? 'unknown';
      final hasUpdate = latestCode > AppVersion.code;

      return DiagnosticCheck(
        title: 'APK publicado',
        target: '/android/version/',
        message: hasUpdate
            ? 'Disponible $latestName ($latestCode), firma $signing'
            : 'Version publicada alineada, firma $signing',
        statusCode: response.statusCode,
        state: signing.contains('debug')
            ? DiagnosticState.warning
            : DiagnosticState.ok,
      );
    } on DioException catch (error) {
      return DiagnosticCheck.fail(
        title: 'APK publicado',
        target: '/android/version/',
        message: _errorMessage(error),
        statusCode: error.response?.statusCode,
      );
    }
  }
}

class DiagnosticsReport {
  const DiagnosticsReport({
    required this.generatedAt,
    required this.appVersionName,
    required this.appVersionCode,
    required this.packageName,
    required this.apiBaseUrl,
    required this.publicBaseUrl,
    required this.hasAccessToken,
    required this.hasRefreshToken,
    required this.checks,
  });

  final DateTime generatedAt;
  final String appVersionName;
  final int appVersionCode;
  final String packageName;
  final String apiBaseUrl;
  final String publicBaseUrl;
  final bool hasAccessToken;
  final bool hasRefreshToken;
  final List<DiagnosticCheck> checks;

  int get okCount =>
      checks.where((check) => check.state == DiagnosticState.ok).length;
  int get warningCount =>
      checks.where((check) => check.state == DiagnosticState.warning).length;
  int get failCount =>
      checks.where((check) => check.state == DiagnosticState.fail).length;

  bool get isHealthy => failCount == 0;
}

class DiagnosticCheck {
  const DiagnosticCheck({
    required this.title,
    required this.target,
    required this.message,
    required this.state,
    this.statusCode,
  });

  const DiagnosticCheck.ok({
    required this.title,
    required this.target,
    required this.message,
    this.statusCode,
  }) : state = DiagnosticState.ok;

  const DiagnosticCheck.fail({
    required this.title,
    required this.target,
    required this.message,
    this.statusCode,
  }) : state = DiagnosticState.fail;

  final String title;
  final String target;
  final String message;
  final DiagnosticState state;
  final int? statusCode;
}

enum DiagnosticState { ok, warning, fail }

String _errorMessage(DioException error) {
  final statusCode = error.response?.statusCode;
  final data = error.response?.data;
  if (data is Map<String, dynamic>) {
    final detail = data['detail'] ?? data['error'] ?? data['status'];
    if (detail != null) {
      return 'HTTP $statusCode: $detail';
    }
  }
  if (statusCode != null) return 'HTTP $statusCode';
  return error.message ?? 'No hubo respuesta del servidor';
}

int _intValue(dynamic value) {
  if (value is int) return value;
  return int.tryParse(value?.toString() ?? '') ?? 0;
}
