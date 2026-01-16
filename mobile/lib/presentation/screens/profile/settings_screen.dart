import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:paddock/data/storage/settings_storage.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final baseUrlAsync = ref.watch(baseUrlOverrideProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: baseUrlAsync.when(
        data: (value) {
          if (_controller.text.isEmpty) {
            _controller.text = value ?? '';
          }
          return Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Base URL (override)'),
                const SizedBox(height: 8),
                TextField(
                  controller: _controller,
                  decoration: const InputDecoration(
                    hintText: 'http://localhost:8000',
                  ),
                ),
                const SizedBox(height: 12),
                ElevatedButton(
                  onPressed: () async {
                    final storage = await ref.read(settingsStorageProvider.future);
                    await storage.writeBaseUrlOverride(_controller.text.trim());
                    ref.invalidate(baseUrlOverrideProvider);
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Base URL mise à jour.')),
                      );
                    }
                  },
                  child: const Text('Enregistrer'),
                ),
                const SizedBox(height: 8),
                Text('Valeur actuelle: ${value ?? 'auto'}'),
              ],
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Erreur: $err')),
      ),
    );
  }
}
