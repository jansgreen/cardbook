import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/network/api_response.dart';
import 'package:mobile_cardbook/core/storage/offline_cache.dart';

final mobileFormsPayloadProvider =
    FutureProvider<MobileFormsPayload>((ref) async {
  final api = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  const cacheKey = 'mobile_forms_payload';
  try {
    final response = await api.dio.get<Map<String, dynamic>>('/mobile/forms/');
    final data = extractData(response.data);
    final payload = MobileFormsPayload.fromJson(data);
    await cache.writeList(cacheKey, [payload.toJson()]);
    return payload;
  } catch (error) {
    final cached =
        shouldUseOfflineCache(error) ? await cache.readList(cacheKey) : null;
    if (cached != null && cached.isNotEmpty) {
      return MobileFormsPayload.fromJson(cached.first);
    }
    rethrow;
  }
});

final mobileFormsProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final payload = await ref.read(mobileFormsPayloadProvider.future);
  return payload.forms;
});

class MobileFormsPayload {
  const MobileFormsPayload({
    required this.forms,
    required this.builderHome,
  });

  final List<Map<String, dynamic>> forms;
  final String builderHome;

  factory MobileFormsPayload.fromJson(Map<String, dynamic> json) {
    final formsValue = json['forms'];
    return MobileFormsPayload(
      forms: formsValue is List
          ? formsValue.whereType<Map<String, dynamic>>().toList()
          : const <Map<String, dynamic>>[],
      builderHome: json['builder_home']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'forms': forms,
      'builder_home': builderHome,
    };
  }
}
