import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/network/api_response.dart';
import 'package:mobile_cardbook/core/storage/offline_cache.dart';

final mobileJobsProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  const cacheKey = 'mobile_jobs';
  try {
    final response = await api.dio.get<Map<String, dynamic>>('/mobile/jobs/');
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

final jobSpecialtiesProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final repository = ref.read(jobRepositoryProvider);
  return repository.specialties();
});

final jobRepositoryProvider = Provider<JobRepository>((ref) {
  return JobRepository(apiClient: ref.read(apiClientProvider));
});

class JobRepository {
  const JobRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<List<Map<String, dynamic>>> specialties() async {
    final response = await _apiClient.dio
        .get<Map<String, dynamic>>('/jobcards/specialties/');
    return extractData(response.data)['results'] is List
        ? (extractData(response.data)['results'] as List<dynamic>)
            .whereType<Map<String, dynamic>>()
            .toList()
        : extractResults(response.data);
  }

  Future<Map<String, dynamic>> create(Map<String, dynamic> payload,
      {String photoPath = ''}) async {
    final data = await _payload(payload, photoPath: photoPath);
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/jobcards/',
      data: data,
    );
    return extractData(response.data);
  }

  Future<Map<String, dynamic>> update(Map<String, dynamic> payload,
      {String photoPath = ''}) async {
    final data = await _payload(payload, photoPath: photoPath);
    final response = await _apiClient.dio.patch<Map<String, dynamic>>(
      '/jobcards/me/',
      data: data,
    );
    return extractData(response.data);
  }

  Future<void> deleteMine() async {
    await _apiClient.dio.delete<Map<String, dynamic>>('/jobcards/me/');
  }

  Future<dynamic> _payload(Map<String, dynamic> payload,
      {required String photoPath}) async {
    final frontPath = payload.remove('_physical_card_front_path')?.toString();
    final backPath = payload.remove('_physical_card_back_path')?.toString();
    if (photoPath.trim().isEmpty &&
        (frontPath == null || frontPath.isEmpty) &&
        (backPath == null || backPath.isEmpty)) {
      return payload;
    }
    final data = Map<String, dynamic>.from(payload);
    if (photoPath.trim().isNotEmpty) {
      data['photo'] = await MultipartFile.fromFile(photoPath);
    }
    if (frontPath != null && frontPath.isNotEmpty) {
      data['physical_card_front_image'] =
          await MultipartFile.fromFile(frontPath);
    }
    if (backPath != null && backPath.isNotEmpty) {
      data['physical_card_back_image'] = await MultipartFile.fromFile(backPath);
    }
    return FormData.fromMap(data);
  }
}
