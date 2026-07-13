import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/network/api_response.dart';

final profileProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final repository = ref.read(profileRepositoryProvider);
  return repository.me();
});

final profileRepositoryProvider = Provider<ProfileRepository>((ref) {
  return ProfileRepository(apiClient: ref.read(apiClientProvider));
});

class ProfileRepository {
  const ProfileRepository({required ApiClient apiClient})
      : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<Map<String, dynamic>> me() async {
    final response =
        await _apiClient.dio.get<Map<String, dynamic>>('/accounts/me/');
    return extractData(response.data);
  }

  Future<Map<String, dynamic>> update(Map<String, dynamic> payload) async {
    final response = await _apiClient.dio
        .patch<Map<String, dynamic>>('/accounts/profile/', data: payload);
    return extractData(response.data);
  }
}
