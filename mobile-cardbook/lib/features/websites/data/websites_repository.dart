import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/network/api_response.dart';
import 'package:mobile_cardbook/core/storage/offline_cache.dart';

final mobileWebsitesProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  const cacheKey = 'mobile_websites';
  try {
    final response =
        await api.dio.get<Map<String, dynamic>>('/mobile/websites/');
    final data = extractListFromData(response.data, 'websites');
    await cache.writeList(cacheKey, data);
    return data;
  } catch (error) {
    final cached =
        shouldUseOfflineCache(error) ? await cache.readList(cacheKey) : null;
    if (cached != null) return cached;
    rethrow;
  }
});
