import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';

final mobileDashboardProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.read(apiClientProvider);
  final response = await api.dio.get<Map<String, dynamic>>('/mobile/dashboard/');
  return response.data?['data'] as Map<String, dynamic>? ?? {};
});
