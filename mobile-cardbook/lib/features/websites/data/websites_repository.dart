import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/network/api_response.dart';
import 'package:mobile_cardbook/core/storage/offline_cache.dart';

final mobileWebsitesProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final payload = await ref.read(mobileWebsitesPayloadProvider.future);
  return payload.websites;
});

final mobileWebsitesPayloadProvider =
    FutureProvider<MobileWebsitesPayload>((ref) async {
  final api = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  const cacheKey = 'mobile_websites_payload';
  try {
    final response =
        await api.dio.get<Map<String, dynamic>>('/mobile/websites/');
    final data = extractData(response.data);
    final payload = MobileWebsitesPayload.fromJson(data);
    await cache.writeList(cacheKey, [payload.toJson()]);
    return payload;
  } catch (error) {
    final cached =
        shouldUseOfflineCache(error) ? await cache.readList(cacheKey) : null;
    if (cached != null && cached.isNotEmpty) {
      return MobileWebsitesPayload.fromJson(cached.first);
    }
    rethrow;
  }
});

class MobileWebsitesPayload {
  const MobileWebsitesPayload({
    required this.websites,
    required this.createLink,
    required this.builderHome,
  });

  final List<Map<String, dynamic>> websites;
  final String createLink;
  final String builderHome;

  factory MobileWebsitesPayload.fromJson(Map<String, dynamic> json) {
    final websitesValue = json['websites'];
    return MobileWebsitesPayload(
      websites: websitesValue is List
          ? websitesValue.whereType<Map<String, dynamic>>().toList()
          : const <Map<String, dynamic>>[],
      createLink: json['create_link']?.toString() ?? '',
      builderHome: json['builder_home']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'websites': websites,
      'create_link': createLink,
      'builder_home': builderHome,
    };
  }
}
