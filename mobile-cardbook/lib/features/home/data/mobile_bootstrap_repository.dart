import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/network/api_client.dart';
import 'package:mobile_cardbook/core/network/api_response.dart';

final mobileBootstrapRepositoryProvider =
    Provider<MobileBootstrapRepository>((ref) {
  return MobileBootstrapRepository(ref.read(apiClientProvider));
});

final mobileBootstrapProvider = FutureProvider<CardbookBootstrap>((ref) async {
  return ref.read(mobileBootstrapRepositoryProvider).fetch();
});

class MobileBootstrapRepository {
  const MobileBootstrapRepository(this._apiClient);

  final ApiClient _apiClient;

  Future<CardbookBootstrap> fetch() async {
    final response =
        await _apiClient.dio.get<Map<String, dynamic>>('/mobile/bootstrap/');
    return CardbookBootstrap.fromJson(extractData(response.data));
  }
}

class CardbookBootstrap {
  const CardbookBootstrap({
    required this.raw,
    required this.user,
    required this.registrationIntent,
    required this.accountType,
    required this.allowedSections,
    required this.menu,
    required this.capabilities,
  });

  final Map<String, dynamic> raw;
  final Map<String, dynamic> user;
  final String registrationIntent;
  final String accountType;
  final Set<String> allowedSections;
  final List<MobileMenuItem> menu;
  final Map<String, dynamic> capabilities;

  factory CardbookBootstrap.fromJson(Map<String, dynamic> json) {
    final menuValue = json['menu'] ?? json['navigation'];
    final sections = json['allowed_sections'];
    return CardbookBootstrap(
      raw: json,
      user: json['user'] is Map<String, dynamic>
          ? json['user'] as Map<String, dynamic>
          : const <String, dynamic>{},
      registrationIntent: json['registration_intent']?.toString() ?? '',
      accountType: json['account_type']?.toString() ?? '',
      allowedSections: sections is List
          ? sections.map((item) => item.toString()).toSet()
          : const <String>{},
      menu: menuValue is List
          ? menuValue
              .whereType<Map<String, dynamic>>()
              .map(MobileMenuItem.fromJson)
              .toList()
          : const <MobileMenuItem>[],
      capabilities: json['capabilities'] is Map<String, dynamic>
          ? json['capabilities'] as Map<String, dynamic>
          : const <String, dynamic>{},
    );
  }

  bool can(String key) => capabilities[key] == true;

  bool allows(String section) => allowedSections.contains(section);

  String get defaultRoute {
    if (accountType == 'job') return '/jobs';
    if (accountType == 'agent') return '/alliances';
    return '/';
  }
}

class MobileMenuItem {
  const MobileMenuItem({
    required this.key,
    required this.label,
    required this.endpoint,
    required this.webUrl,
    required this.availableNative,
  });

  final String key;
  final String label;
  final String endpoint;
  final String webUrl;
  final bool availableNative;

  factory MobileMenuItem.fromJson(Map<String, dynamic> json) {
    return MobileMenuItem(
      key: json['key']?.toString() ?? '',
      label: json['label']?.toString() ?? '',
      endpoint: json['endpoint']?.toString() ?? '',
      webUrl: json['web_url']?.toString() ?? '',
      availableNative: json['available_native'] == true,
    );
  }
}

bool capability(Map<String, dynamic> bootstrap, String key) {
  final capabilities = bootstrap['capabilities'];
  if (capabilities is! Map<String, dynamic>) return false;
  return capabilities[key] == true;
}
