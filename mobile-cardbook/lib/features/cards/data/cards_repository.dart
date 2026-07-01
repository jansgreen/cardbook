import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/network/api_response.dart';

final digitalCardsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.read(apiClientProvider);
  final response = await api.dio.get<Map<String, dynamic>>('/cards/');
  return extractResults(response.data);
});

final businessCardsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.read(apiClientProvider);
  final response = await api.dio.get<Map<String, dynamic>>('/cards/business-cards/');
  return extractResults(response.data);
});

final cardRepositoryProvider = Provider<CardRepository>((ref) {
  return CardRepository(apiClient: ref.read(apiClientProvider));
});

class CardRepository {
  const CardRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<Map<String, dynamic>> createDigital(Map<String, dynamic> payload) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>('/cards/', data: payload);
    return extractData(response.data);
  }

  Future<Map<String, dynamic>> updateDigital(int id, Map<String, dynamic> payload) async {
    final response = await _apiClient.dio.patch<Map<String, dynamic>>('/cards/$id/', data: payload);
    return extractData(response.data);
  }

  Future<void> deleteDigital(int id) async {
    await _apiClient.dio.delete<Map<String, dynamic>>('/cards/$id/');
  }

  Future<Map<String, dynamic>> createBusiness(Map<String, dynamic> payload) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>('/cards/business-cards/', data: payload);
    return extractData(response.data);
  }

  Future<Map<String, dynamic>> updateBusiness(int id, Map<String, dynamic> payload) async {
    final response = await _apiClient.dio.patch<Map<String, dynamic>>('/cards/business-cards/$id/', data: payload);
    return extractData(response.data);
  }

  Future<void> deleteBusiness(int id) async {
    await _apiClient.dio.delete<Map<String, dynamic>>('/cards/business-cards/$id/');
  }
}
