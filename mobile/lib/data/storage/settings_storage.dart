import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _baseUrlKey = 'base_url_override';

class SettingsStorage {
  SettingsStorage(this._prefs);

  final SharedPreferences _prefs;

  String? readBaseUrlOverride() => _prefs.getString(_baseUrlKey);

  Future<void> writeBaseUrlOverride(String? value) async {
    if (value == null || value.isEmpty) {
      await _prefs.remove(_baseUrlKey);
    } else {
      await _prefs.setString(_baseUrlKey, value);
    }
  }
}

final sharedPreferencesProvider = FutureProvider<SharedPreferences>((ref) async {
  return SharedPreferences.getInstance();
});

final settingsStorageProvider = FutureProvider<SettingsStorage>((ref) async {
  final prefs = await ref.watch(sharedPreferencesProvider.future);
  return SettingsStorage(prefs);
});

final baseUrlOverrideProvider = FutureProvider<String?>((ref) async {
  final storage = await ref.watch(settingsStorageProvider.future);
  return storage.readBaseUrlOverride();
});
