List<Map<String, dynamic>> extractResults(dynamic responseBody) {
  if (responseBody is! Map<String, dynamic>) return [];
  final data = responseBody['data'];
  if (data is List) {
    return data.whereType<Map<String, dynamic>>().toList();
  }
  if (data is Map<String, dynamic>) {
    final results = data['results'];
    if (results is List) {
      return results.whereType<Map<String, dynamic>>().toList();
    }
  }
  return [];
}

Map<String, dynamic> extractData(dynamic responseBody) {
  if (responseBody is! Map<String, dynamic>) return {};
  final data = responseBody['data'];
  return data is Map<String, dynamic> ? data : {};
}
