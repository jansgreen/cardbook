import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/network/api_response.dart';

final referralNotificationsProvider =
    FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.read(apiClientProvider);
  final response =
      await api.dio.get<Map<String, dynamic>>('/referrals/notifications/');
  return extractData(response.data);
});

final alliancesProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.read(apiClientProvider);
  final response = await api.dio.get<Map<String, dynamic>>('/alliances/');
  return extractResults(response.data);
});

final notificationRepositoryProvider = Provider<NotificationRepository>((ref) {
  return NotificationRepository(apiClient: ref.read(apiClientProvider));
});

final allianceRepositoryProvider = Provider<AllianceRepository>((ref) {
  return AllianceRepository(apiClient: ref.read(apiClientProvider));
});

class NotificationRepository {
  const NotificationRepository({required ApiClient apiClient})
      : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<Map<String, dynamic>> markAllRead() async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/referrals/notifications/mark-read/',
    );
    return extractData(response.data);
  }

  Future<Map<String, dynamic>> markRead(int id) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/referrals/notifications/$id/mark-read/',
    );
    return extractData(response.data);
  }
}

class AllianceRepository {
  const AllianceRepository({required ApiClient apiClient})
      : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<Map<String, dynamic>> requestAlliance({
    required int requesterId,
    required int receiverId,
  }) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/alliances/',
      data: {'requester': requesterId, 'receiver': receiverId},
    );
    return extractData(response.data);
  }

  Future<Map<String, dynamic>> decide({
    required int allianceId,
    required String decision,
  }) async {
    final response = await _apiClient.dio
        .post<Map<String, dynamic>>('/alliances/$allianceId/$decision/');
    return extractData(response.data);
  }
}
