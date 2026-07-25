import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/network/api_response.dart';
import 'package:mobile_cardbook/core/storage/offline_cache.dart';

final mobileAIAgentsRepositoryProvider =
    Provider<MobileAIAgentsRepository>((ref) {
  return MobileAIAgentsRepository(ref.read(apiClientProvider));
});

final mobileAIAgentsPayloadProvider =
    FutureProvider<MobileAIAgentsPayload>((ref) async {
  final repository = ref.read(mobileAIAgentsRepositoryProvider);
  final cache = ref.read(offlineCacheProvider);
  const cacheKey = 'mobile_ai_agents_payload';
  try {
    final payload = await repository.fetch();
    await cache.writeList(cacheKey, [payload.toJson()]);
    return payload;
  } catch (error) {
    final cached =
        shouldUseOfflineCache(error) ? await cache.readList(cacheKey) : null;
    if (cached != null && cached.isNotEmpty) {
      return MobileAIAgentsPayload.fromJson(cached.first);
    }
    rethrow;
  }
});

class MobileAIAgentsRepository {
  const MobileAIAgentsRepository(this._apiClient);

  final ApiClient _apiClient;

  Future<MobileAIAgentsPayload> fetch() async {
    final response =
        await _apiClient.dio.get<Map<String, dynamic>>('/mobile/ai-agents/');
    return MobileAIAgentsPayload.fromJson(extractData(response.data));
  }

  Future<Map<String, dynamic>> testQuestion(
      int agentId, String question) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/ai-agents/$agentId/test/',
      data: {'question': question},
    );
    return extractData(response.data);
  }
}

class MobileAIAgentsPayload {
  const MobileAIAgentsPayload({
    required this.agents,
    required this.dashboardUrl,
    required this.apiUrl,
  });

  final List<Map<String, dynamic>> agents;
  final String dashboardUrl;
  final String apiUrl;

  factory MobileAIAgentsPayload.fromJson(Map<String, dynamic> json) {
    final agentsValue = json['agents'];
    return MobileAIAgentsPayload(
      agents: agentsValue is List
          ? agentsValue.whereType<Map<String, dynamic>>().toList()
          : const <Map<String, dynamic>>[],
      dashboardUrl: json['dashboard_url']?.toString() ?? '',
      apiUrl: json['api_url']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'agents': agents,
      'dashboard_url': dashboardUrl,
      'api_url': apiUrl,
    };
  }
}
