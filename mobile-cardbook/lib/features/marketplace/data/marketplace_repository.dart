import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/network/api_response.dart';
import 'package:mobile_cardbook/core/storage/offline_cache.dart';

final marketplaceQueryProvider = StateProvider<String>((ref) => '');

final marketplaceProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final query = ref.watch(marketplaceQueryProvider).trim();
  final repository = ref.read(marketplaceRepositoryProvider);
  return repository.fetch(query: query);
});

final marketplaceRepositoryProvider = Provider<MarketplaceRepository>((ref) {
  return MarketplaceRepository(
    apiClient: ref.read(apiClientProvider),
    cache: ref.read(offlineCacheProvider),
  );
});

class MarketplaceRepository {
  const MarketplaceRepository({
    required ApiClient apiClient,
    required OfflineCache cache,
  })  : _apiClient = apiClient,
        _cache = cache;

  final ApiClient _apiClient;
  final OfflineCache _cache;

  Future<Map<String, dynamic>> fetch({String query = ''}) async {
    final cacheKey = query.isEmpty ? 'marketplace' : 'marketplace_$query';
    try {
      final response = await _apiClient.dio.get<Map<String, dynamic>>(
        '/marketplace/',
        queryParameters: {
          if (query.isNotEmpty) 'q': query,
          'limit': 24,
        },
      );
      final data = extractData(response.data);
      await _cache.writeMap(cacheKey, data);
      return data;
    } catch (error) {
      final cached =
          shouldUseOfflineCache(error) ? await _cache.readMap(cacheKey) : null;
      if (cached != null) return cached;
      rethrow;
    }
  }
}
