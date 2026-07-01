import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/network/api_response.dart';

final companiesProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.read(apiClientProvider);
  final response = await api.dio.get<Map<String, dynamic>>('/companies/');
  return extractResults(response.data);
});

final recommendedCompaniesProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.read(apiClientProvider);
  final response = await api.dio.get<Map<String, dynamic>>('/companies/recommendations/');
  return extractResults(response.data);
});

final companyRepositoryProvider = Provider<CompanyRepository>((ref) {
  return CompanyRepository(apiClient: ref.read(apiClientProvider));
});

class CompanyRepository {
  const CompanyRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<Map<String, dynamic>> create(Map<String, dynamic> payload) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>('/companies/', data: payload);
    return extractData(response.data);
  }

  Future<Map<String, dynamic>> update(int id, Map<String, dynamic> payload) async {
    final response = await _apiClient.dio.patch<Map<String, dynamic>>('/companies/$id/', data: payload);
    return extractData(response.data);
  }

  Future<void> delete(int id) async {
    await _apiClient.dio.delete<Map<String, dynamic>>('/companies/$id/');
  }
}
