import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/network/api_response.dart';
import 'package:mobile_cardbook/core/storage/offline_cache.dart';

final bookProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  const cacheKey = 'mobile_book_businesses';
  try {
    final response = await api.dio.get<Map<String, dynamic>>('/mobile/book/');
    final data = extractListFromData(response.data, 'businesses');
    await cache.writeList(cacheKey, data);
    return data;
  } catch (error) {
    final cached =
        shouldUseOfflineCache(error) ? await cache.readList(cacheKey) : null;
    if (cached != null) return cached;
    rethrow;
  }
});

final mobileBookProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  const cacheKey = 'mobile_book';
  try {
    final response = await api.dio.get<Map<String, dynamic>>('/mobile/book/');
    final data = extractData(response.data);
    await cache.writeMap(cacheKey, data);
    return data;
  } catch (error) {
    final cached =
        shouldUseOfflineCache(error) ? await cache.readMap(cacheKey) : null;
    if (cached != null) return cached;
    rethrow;
  }
});

final bookRepositoryProvider = Provider<BookRepository>((ref) {
  return BookRepository(apiClient: ref.read(apiClientProvider));
});

class BookRepository {
  const BookRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<Map<String, dynamic>> saveCompany(int companyId,
      {String notes = ''}) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/book/',
      data: {'company': companyId, 'notes': notes},
    );
    return extractData(response.data);
  }

  Future<Map<String, dynamic>> saveDigitalCard(int cardId,
      {String notes = ''}) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/book/',
      data: {'digital_card': cardId, 'notes': notes},
    );
    return extractData(response.data);
  }

  Future<Map<String, dynamic>> saveBusinessCard(int cardId,
      {String notes = ''}) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/book/',
      data: {'business_card': cardId, 'notes': notes},
    );
    return extractData(response.data);
  }

  Future<void> remove(int id) async {
    await _apiClient.dio.delete<Map<String, dynamic>>('/book/$id/');
  }

  Future<Map<String, dynamic>> saveCandidate({
    required int companyId,
    required int jobCardId,
    String notes = '',
  }) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/book/save/',
      data: {'company': companyId, 'job_card': jobCardId, 'notes': notes},
    );
    return extractData(response.data);
  }

  Future<void> removeCandidate(int id) async {
    await _apiClient.dio.delete<Map<String, dynamic>>('/book/save/$id/');
  }
}
