import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/network/api_response.dart';

final bookProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.read(apiClientProvider);
  final response = await api.dio.get<Map<String, dynamic>>('/book/');
  return extractResults(response.data);
});

final bookRepositoryProvider = Provider<BookRepository>((ref) {
  return BookRepository(apiClient: ref.read(apiClientProvider));
});

class BookRepository {
  const BookRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<Map<String, dynamic>> saveCompany(int companyId, {String notes = ''}) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/book/',
      data: {'company': companyId, 'notes': notes},
    );
    return extractData(response.data);
  }

  Future<void> remove(int id) async {
    await _apiClient.dio.delete<Map<String, dynamic>>('/book/$id/');
  }
}
