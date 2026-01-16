import 'package:paddock/data/api_client.dart';

class ApiException implements Exception {
  ApiException(this.message);

  final String message;

  factory ApiException.fromResponse(response) {
    String message = 'Une erreur est survenue.';
    try {
      final body = decodeJson(response.body);
      message = body['detail']?.toString() ?? message;
    } catch (_) {}
    return ApiException(message);
  }
}
