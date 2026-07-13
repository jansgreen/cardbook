import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/config/api_config.dart';
import 'package:mobile_cardbook/core/config/app_version.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/network/api_response.dart';

final supportRepositoryProvider = Provider<SupportRepository>((ref) {
  return SupportRepository(apiClient: ref.read(apiClientProvider));
});

final supportTicketsProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  return ref.read(supportRepositoryProvider).listTickets();
});

class SupportRepository {
  const SupportRepository({required ApiClient apiClient})
      : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<List<Map<String, dynamic>>> listTickets() async {
    final response =
        await _apiClient.dio.get<Map<String, dynamic>>('/support/tickets/');
    return extractResults(response.data);
  }

  Future<Map<String, dynamic>> createTicket({
    required String category,
    required String priority,
    required String subject,
    required String message,
  }) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/support/tickets/',
      data: {
        'category': category,
        'priority': priority,
        'subject': subject,
        'message': message,
        'technical_context': {
          'source': 'flutter',
          'package': AppVersion.packageName,
          'version_name': AppVersion.name,
          'version_code': AppVersion.code,
          'api_base_url': ApiConfig.apiBase,
          'public_base_url': ApiConfig.publicBase,
          'created_from': 'mobile_support_center',
        },
      },
    );
    return extractData(response.data);
  }
}
