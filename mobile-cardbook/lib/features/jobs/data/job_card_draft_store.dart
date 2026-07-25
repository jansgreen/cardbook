import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/storage/offline_cache.dart';

final jobCardDraftStoreProvider = Provider<JobCardDraftStore>((ref) {
  return JobCardDraftStore(ref.read(offlineCacheProvider));
});

final jobCardDraftProvider = FutureProvider<JobCardDraft?>((ref) {
  return ref.read(jobCardDraftStoreProvider).read();
});

class JobCardDraftStore {
  const JobCardDraftStore(this._cache);

  static const _cacheKey = 'white_card_job_draft';
  final OfflineCache _cache;

  Future<JobCardDraft?> read() async {
    final data = await _cache.readMap(_cacheKey);
    if (data == null || data.isEmpty) return null;
    final draft = JobCardDraft.fromJson(data);
    return draft.hasContent ? draft : null;
  }

  Future<void> save(JobCardDraft draft) async {
    await _cache.writeMap(_cacheKey, draft.toJson());
  }

  Future<void> clear() => _cache.remove(_cacheKey);
}

class JobCardDraft {
  const JobCardDraft({
    required this.title,
    required this.phone,
    required this.address,
    required this.linkedin,
    required this.resume,
    required this.description,
    required this.experience,
    required this.languages,
    required this.technologies,
    required this.certifications,
    required this.availability,
    required this.isAvailable,
    required this.photoPath,
    required this.frontScanPath,
    required this.backScanPath,
    required this.updatedAt,
    this.specialtyId,
  });

  final int? specialtyId;
  final String title;
  final String phone;
  final String address;
  final String linkedin;
  final String resume;
  final String description;
  final String experience;
  final String languages;
  final String technologies;
  final String certifications;
  final String availability;
  final bool isAvailable;
  final String photoPath;
  final String frontScanPath;
  final String backScanPath;
  final DateTime updatedAt;

  bool get hasContent {
    return specialtyId != null ||
        [
          title,
          phone,
          address,
          linkedin,
          resume,
          description,
          experience,
          languages,
          technologies,
          certifications,
          availability,
          photoPath,
          frontScanPath,
          backScanPath,
        ].any((value) => value.trim().isNotEmpty);
  }

  factory JobCardDraft.fromJson(Map<String, dynamic> json) {
    return JobCardDraft(
      specialtyId: _intValue(json['specialty_id']),
      title: _text(json['title']),
      phone: _text(json['phone']),
      address: _text(json['address']),
      linkedin: _text(json['linkedin']),
      resume: _text(json['resume']),
      description: _text(json['description']),
      experience: _text(json['experience']),
      languages: _text(json['languages']),
      technologies: _text(json['technologies']),
      certifications: _text(json['certifications']),
      availability: _text(json['availability']),
      isAvailable: json['is_available'] != false,
      photoPath: _text(json['photo_path']),
      frontScanPath: _text(json['front_scan_path']),
      backScanPath: _text(json['back_scan_path']),
      updatedAt: DateTime.tryParse(_text(json['updated_at'])) ?? DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'specialty_id': specialtyId,
      'title': title,
      'phone': phone,
      'address': address,
      'linkedin': linkedin,
      'resume': resume,
      'description': description,
      'experience': experience,
      'languages': languages,
      'technologies': technologies,
      'certifications': certifications,
      'availability': availability,
      'is_available': isAvailable,
      'photo_path': photoPath,
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
