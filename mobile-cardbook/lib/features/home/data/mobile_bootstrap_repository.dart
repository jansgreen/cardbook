import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/network/api_response.dart';

final mobileBootstrapProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.read(apiClientProvider);
  final response = await api.dio.get<Map<String, dynamic>>('/mobile/bootstrap/');
  return extractData(response.data);
});

bool capability(Map<String, dynamic> bootstrap, String key) {
  final capabilities = bootstrap['capabilities'];
  if (capabilities is! Map<String, dynamic>) return false;
  return capabilities[key] == true;
}
