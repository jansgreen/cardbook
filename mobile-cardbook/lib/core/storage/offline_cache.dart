import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';

final offlineCacheProvider = Provider<OfflineCache>((ref) => OfflineCache());

class OfflineCache {
  const OfflineCache();

  Future<Map<String, dynamic>?> readMap(String key) async {
    final file = await _fileFor(key);
    if (!await file.exists()) return null;
    final raw = await file.readAsString();
    final decoded = jsonDecode(raw);
    if (decoded is Map<String, dynamic>) {
      return Map<String, dynamic>.from(decoded)..['_offline'] = true;
    }
    return null;
  }

  Future<List<Map<String, dynamic>>?> readList(String key) async {
    final file = await _fileFor(key);
    if (!await file.exists()) return null;
    final raw = await file.readAsString();
    final decoded = jsonDecode(raw);
    if (decoded is List) {
      return decoded.whereType<Map<String, dynamic>>().toList();
    }
    return null;
  }

  Future<void> writeMap(String key, Map<String, dynamic> value) async {
    final file = await _fileFor(key);
    final clean = Map<String, dynamic>.from(value)..remove('_offline');
    await file.writeAsString(jsonEncode(clean), flush: true);
  }

  Future<void> writeList(String key, List<Map<String, dynamic>> value) async {
    final file = await _fileFor(key);
    await file.writeAsString(jsonEncode(value), flush: true);
  }

  Future<File> _fileFor(String key) async {
    final directory = await getApplicationSupportDirectory();
    final cacheDirectory =
        Directory('${directory.path}${Platform.pathSeparator}offline_cache');
    if (!await cacheDirectory.exists()) {
      await cacheDirectory.create(recursive: true);
    }
    return File(
        '${cacheDirectory.path}${Platform.pathSeparator}${_safeKey(key)}.json');
  }

  String _safeKey(String key) {
    return key.replaceAll(RegExp(r'[^a-zA-Z0-9_-]+'), '_');
  }
}

bool shouldUseOfflineCache(Object error) {
  if (error is DioException) {
    final statusCode = error.response?.statusCode;
    if (statusCode == 401 || statusCode == 403) return false;
  }
  return true;
}
