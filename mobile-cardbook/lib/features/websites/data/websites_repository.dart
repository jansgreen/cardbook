import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/network/api_response.dart';

final mobileWebsitesProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.read(apiClientProvider);
  final response = await api.dio.get<Map<String, dynamic>>('/mobile/websites/');
  return extractListFromData(response.data, 'websites');
});
