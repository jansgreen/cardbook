import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/config/api_config.dart';
import 'package:mobile_cardbook/core/storage/token_storage.dart';

final tokenStorageProvider = Provider<TokenStorage>((ref) => TokenStorage());

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(ref.read(tokenStorageProvider));
});

class ApiClient {
  ApiClient(this._tokenStorage)
      : dio = Dio(
          BaseOptions(
            baseUrl: ApiConfig.apiBase,
            connectTimeout: const Duration(seconds: 12),
            receiveTimeout: const Duration(seconds: 18),
            headers: {'Accept': 'application/json'},
          ),
        ) {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _tokenStorage.readAccess();
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          final statusCode = error.response?.statusCode;
          final alreadyRetried = error.requestOptions.extra['retried'] == true;
          if (statusCode == 401 && !alreadyRetried && await _refreshToken()) {
            final request = error.requestOptions;
            request.extra['retried'] = true;
            final access = await _tokenStorage.readAccess();
            request.headers['Authorization'] = 'Bearer $access';
            try {
              final response = await dio.fetch<dynamic>(request);
              return handler.resolve(response);
            } catch (_) {
              return handler.next(error);
            }
          }
          handler.next(error);
        },
      ),
    );
  }

  final TokenStorage _tokenStorage;
  final Dio dio;

  Future<bool> _refreshToken() async {
    final refresh = await _tokenStorage.readRefresh();
    if (refresh == null || refresh.isEmpty) return false;
    try {
      final response = await Dio(BaseOptions(baseUrl: ApiConfig.apiBase))
          .post<Map<String, dynamic>>(
        '/accounts/token/refresh/',
        data: {'refresh': refresh},
      );
      final access = response.data?['access'] as String?;
      final newRefresh = response.data?['refresh'] as String? ?? refresh;
      if (access == null) return false;
      await _tokenStorage.save(access: access, refresh: newRefresh);
      return true;
    } catch (_) {
      await _tokenStorage.clear();
      return false;
    }
  }
}
