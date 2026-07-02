import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/storage/token_storage.dart';

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(
    apiClient: ref.read(apiClientProvider),
    tokenStorage: ref.read(tokenStorageProvider),
  );
});

class AuthRepository {
  AuthRepository({required ApiClient apiClient, required TokenStorage tokenStorage})
      : _apiClient = apiClient,
        _tokenStorage = tokenStorage;

  final ApiClient _apiClient;
  final TokenStorage _tokenStorage;

  Future<Map<String, dynamic>> login({required String username, required String password}) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/accounts/login/',
      data: {'username': username, 'password': password},
    );
    final data = response.data?['data'] as Map<String, dynamic>? ?? {};
    final tokens = data['tokens'] as Map<String, dynamic>? ?? {};
    final access = tokens['access'] as String?;
    final refresh = tokens['refresh'] as String?;
    if (access == null || refresh == null) {
      throw StateError('La API no devolvio tokens validos.');
    }
    await _tokenStorage.save(access: access, refresh: refresh);
    return data['user'] as Map<String, dynamic>? ?? {};
  }

  Future<Map<String, dynamic>> register({
    required String username,
    required String email,
    required String password,
    required String passwordConfirm,
    String firstName = '',
    String lastName = '',
  }) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/accounts/register/',
      data: {
        'username': username,
        'email': email,
        'password': password,
        'password_confirm': passwordConfirm,
        'first_name': firstName,
        'last_name': lastName,
        'preferred_language': 'es',
      },
    );
    final data = response.data?['data'] as Map<String, dynamic>? ?? {};
    final tokens = data['tokens'] as Map<String, dynamic>? ?? {};
    final access = tokens['access'] as String?;
    final refresh = tokens['refresh'] as String?;
    if (access == null || refresh == null) {
      throw StateError('La API no devolvio tokens validos.');
    }
    await _tokenStorage.save(access: access, refresh: refresh);
    return data['user'] as Map<String, dynamic>? ?? {};
  }

  Future<bool> hasStoredSession() async {
    final access = await _tokenStorage.readAccess();
    return access != null && access.isNotEmpty;
  }

  Future<void> logout() async {
    final refresh = await _tokenStorage.readRefresh();
    if (refresh != null && refresh.isNotEmpty) {
      try {
        await _apiClient.dio.post<Map<String, dynamic>>(
          '/accounts/logout/',
          data: {'refresh': refresh},
        );
      } catch (_) {
        // Local logout still matters if the server token blacklist fails.
      }
    }
    await _tokenStorage.clear();
  }
}
