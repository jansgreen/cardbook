import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/storage/offline_cache.dart';

final mobileDashboardProvider =
    FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  const cacheKey = 'mobile_dashboard';
  try {
    final response =
        await api.dio.get<Map<String, dynamic>>('/mobile/dashboard/');
    final data = response.data?['data'] as Map<String, dynamic>? ?? {};
    await cache.writeMap(cacheKey, data);
    return data;
  } catch (error) {
    final cached =
        shouldUseOfflineCache(error) ? await cache.readMap(cacheKey) : null;
    if (cached != null) return cached;
    rethrow;
  }
});
