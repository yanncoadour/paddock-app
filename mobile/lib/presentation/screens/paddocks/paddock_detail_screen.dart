import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:paddock/domain/models/paddock.dart';
import 'package:paddock/presentation/providers.dart';

class PaddockDetailScreen extends ConsumerWidget {
  const PaddockDetailScreen({super.key, required this.paddockId});

  final int paddockId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final paddockAsync = ref.watch(paddockDetailProvider(paddockId));

    return Scaffold(
      appBar: AppBar(title: const Text('Paddock')),
      body: paddockAsync.when(
        data: (paddock) => _PaddockDetail(paddock: paddock),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Erreur: $err')),
      ),
    );
  }
}

class _PaddockDetail extends ConsumerWidget {
  const _PaddockDetail({required this.paddock});

  final Paddock paddock;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(paddock.name, style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 8),
        Text('Saison ${paddock.seasonYear}'),
        const SizedBox(height: 8),
        Row(
          children: [
            Text('Statut: ${paddock.status}'),
            const SizedBox(width: 12),
            if (paddock.status == 'locked') const Icon(Icons.lock) else const Icon(Icons.lock_open),
          ],
        ),
        const SizedBox(height: 8),
        Text('Code invitation: ${paddock.joinCode}'),
        const SizedBox(height: 24),
        if (paddock.status != 'locked')
          ElevatedButton.icon(
            onPressed: () async {
              try {
                await ref.read(paddockRepositoryProvider).lockPaddock(paddock.id);
                ref.invalidate(paddockDetailProvider(paddock.id));
                ref.invalidate(paddocksProvider);
              } catch (error) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text(error.toString())),
                  );
                }
              }
            },
            icon: const Icon(Icons.lock),
            label: const Text('Verrouiller le paddock'),
          ),
      ],
    );
  }
}
