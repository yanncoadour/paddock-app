import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:paddock/data/storage/settings_storage.dart';

const _defaultBaseUrl = 'http://localhost:8000';
const _iosSimulatorBaseUrl = 'http://127.0.0.1:8000';

class AppConfig {
  final String baseUrl;

  const AppConfig({required this.baseUrl});
}

final appConfigProvider = Provider<AppConfig>((ref) {
  final baseUrl = ref.watch(baseUrlProvider);
  return AppConfig(baseUrl: baseUrl);
});

final baseUrlProvider = Provider<String>((ref) {
  final override = ref.watch(baseUrlOverrideProvider).value;
  if (override != null && override.isNotEmpty) {
    return override;
  }

  if (kIsWeb) {
    return _defaultBaseUrl;
  }

  if (Platform.isIOS) {
    return _iosSimulatorBaseUrl;
  }

  return _defaultBaseUrl;
});
