import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/config/api_config.dart';
import 'package:mobile_cardbook/core/config/app_version.dart';

final appUpdateProvider = FutureProvider<AppUpdateInfo>((ref) async {
  final repository = ref.read(appUpdateRepositoryProvider);
  return repository.check();
});

final appUpdateRepositoryProvider = Provider<AppUpdateRepository>((ref) {
  return AppUpdateRepository();
});

class AppUpdateRepository {
  AppUpdateRepository({Dio? dio}) : _dio = dio ?? Dio();

  final Dio _dio;

  Future<AppUpdateInfo> check() async {
    final response = await _dio.get<Map<String, dynamic>>('${ApiConfig.publicBase}/android/version/');
    final data = response.data ?? {};
    return AppUpdateInfo.fromJson(data);
  }
}

class AppUpdateInfo {
  const AppUpdateInfo({
    required this.latestVersionCode,
    required this.latestVersionName,
    required this.minSupportedVersionCode,
    required this.forceUpdate,
    required this.downloadUrl,
    required this.releasePageUrl,
    required this.message,
    required this.changelog,
  });

  final int latestVersionCode;
  final String latestVersionName;
  final int minSupportedVersionCode;
  final bool forceUpdate;
  final String downloadUrl;
  final String releasePageUrl;
  final String message;
  final List<String> changelog;

  bool get hasUpdate => latestVersionCode > AppVersion.code;
  bool get isUnsupported => AppVersion.code < minSupportedVersionCode;

  factory AppUpdateInfo.fromJson(Map<String, dynamic> json) {
    return AppUpdateInfo(
      latestVersionCode: _intValue(json['latest_version_code']),
      latestVersionName: json['latest_version_name']?.toString() ?? '',
      minSupportedVersionCode: _intValue(json['min_supported_version_code']),
      forceUpdate: json['force_update'] == true,
      downloadUrl: json['download_url']?.toString() ?? '',
      releasePageUrl: json['release_page_url']?.toString() ?? '',
      message: json['message']?.toString() ?? 'Nueva version disponible.',
      changelog: (json['changelog'] as List<dynamic>? ?? []).map((item) => item.toString()).toList(),
    );
  }
}

int _intValue(dynamic value) {
  if (value is int) return value;
  return int.tryParse(value?.toString() ?? '') ?? 0;
}
