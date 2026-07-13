import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/config/app_version.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/network/api_response.dart';

final pushRepositoryProvider = Provider<PushRepository>((ref) {
  return PushRepository(apiClient: ref.read(apiClientProvider));
});

class PushRepository {
  const PushRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<Map<String, dynamic>> devices() async {
    final response =
        await _apiClient.dio.get<Map<String, dynamic>>('/push/devices/');
    return extractData(response.data);
  }

  Future<Map<String, dynamic>> registerDevice({
    required String token,
    String deviceId = '',
  }) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/push/devices/',
      data: {
        'token': token,
        'platform': Platform.isAndroid ? 'android' : 'ios',
        'device_id': deviceId,
        'app_version': '${AppVersion.name}+${AppVersion.code}',
      },
    );
    return extractData(response.data);
  }

  Future<Map<String, dynamic>> disableDevice({required String token}) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/push/devices/disable/',
      data: {'token': token},
    );
    return extractData(response.data);
  }

  Future<Map<String, dynamic>> sendTest() async {
    final response =
        await _apiClient.dio.post<Map<String, dynamic>>('/push/test/');
    return extractData(response.data);
  }
}
