import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/storage/offline_cache.dart';

final businessCardDraftStoreProvider = Provider<BusinessCardDraftStore>((ref) {
  return BusinessCardDraftStore(ref.read(offlineCacheProvider));
});

final businessCardDraftProvider = FutureProvider<BusinessCardDraft?>((ref) {
  return ref.read(businessCardDraftStoreProvider).read();
});

class BusinessCardDraftStore {
  const BusinessCardDraftStore(this._cache);

  static const _cacheKey = 'business_card_import_draft';
  final OfflineCache _cache;

  Future<BusinessCardDraft?> read() async {
    final data = await _cache.readMap(_cacheKey);
    if (data == null || data.isEmpty) return null;
    final draft = BusinessCardDraft.fromJson(data);
    return draft.hasContent ? draft : null;
  }

  Future<void> save(BusinessCardDraft draft) async {
    await _cache.writeMap(_cacheKey, draft.toJson());
  }

  Future<void> clear() => _cache.remove(_cacheKey);
}

class BusinessCardDraft {
  const BusinessCardDraft({
    required this.displayName,
    required this.jobTitle,
    required this.companyName,
    required this.phone,
    required this.email,
    required this.website,
    required this.address,
    required this.tagline,
    required this.services,
    required this.frontScanPath,
    required this.backScanPath,
    required this.updatedAt,
    this.profileId,
    this.companyId,
  });

  final int? profileId;
  final int? companyId;
  final String displayName;
  final String jobTitle;
  final String companyName;
  final String phone;
  final String email;
  final String website;
  final String address;
  final String tagline;
  final String services;
  final String frontScanPath;
  final String backScanPath;
  final DateTime updatedAt;

  bool get hasContent {
    return [
      displayName,
      jobTitle,
      companyName,
      phone,
      email,
      website,
      address,
      tagline,
      services,
      frontScanPath,
      backScanPath,
    ].any((value) => value.trim().isNotEmpty);
  }

  factory BusinessCardDraft.fromJson(Map<String, dynamic> json) {
    return BusinessCardDraft(
      profileId: _intValue(json['profile_id']),
      companyId: _intValue(json['company_id']),
      displayName: _text(json['display_name']),
      jobTitle: _text(json['job_title']),
      companyName: _text(json['company_name']),
      phone: _text(json['phone']),
      email: _text(json['email']),
      website: _text(json['website']),
      address: _text(json['address']),
      tagline: _text(json['tagline']),
      services: _text(json['services']),
      frontScanPath: _text(json['front_scan_path']),
      backScanPath: _text(json['back_scan_path']),
      updatedAt: DateTime.tryParse(_text(json['updated_at'])) ?? DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'profile_id': profileId,
      'company_id': companyId,
      'display_name': displayName,
      'job_title': jobTitle,
      'company_name': companyName,
      'phone': phone,
      'email': email,
      'website': website,
      'address': address,
      'tagline': tagline,
      'services': services,
      'front_scan_path': frontScanPath,
      'back_scan_path': backScanPath,
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}

String _text(dynamic value) => value?.toString().trim() ?? '';

int? _intValue(dynamic value) {
  if (value is int) return value;
  return int.tryParse(value?.toString() ?? '');
}
