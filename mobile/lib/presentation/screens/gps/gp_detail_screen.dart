import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:paddock/core/utils/date_format.dart';
import 'package:paddock/presentation/providers.dart';

class GpDetailScreen extends ConsumerWidget {
  const GpDetailScreen({super.key, required this.gpId});

  final int gpId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final gpAsync = ref.watch(gpDetailProvider(gpId));

    return Scaffold(
      appBar: AppBar(title: const Text('Détail GP')),
      body: gpAsync.when(
        data: (gp) {
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text(
                'Round ${gp.roundNumber} · ${gp.name}',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: 8),
              Text(gp.country),
              const SizedBox(height: 8),
              Row(
                children: [
                  Text('Course: ${formatFrenchDateTime(gp.startsAtUtc)}'),
                  const SizedBox(width: 12),
                  if (gp.hasSprint)
                    const Chip(
                      label: Text('Sprint'),
                      visualDensity: VisualDensity.compact,
                    ),
                ],
              ),
              const SizedBox(height: 16),
              Text('Sessions', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              ...gp.sessions.map(
                (session) => Card(
                  child: ListTile(
                    title: Text(session.type),
                    subtitle: Text(formatFrenchDateTime(session.deadlineUtc)),
                    trailing: Text(session.status),
                  ),
                ),
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Erreur: $err')),
      ),
    );
  }
}
