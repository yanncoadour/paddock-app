import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:paddock/domain/models/standing.dart';
import 'package:paddock/presentation/providers.dart';

class StandingsScreen extends ConsumerStatefulWidget {
  const StandingsScreen({super.key});

  @override
  ConsumerState<StandingsScreen> createState() => _StandingsScreenState();
}

class _StandingsScreenState extends ConsumerState<StandingsScreen> {
  int _seasonId = 2026;
  int? _selectedPaddockId;

  @override
  Widget build(BuildContext context) {
    final paddocksAsync = ref.watch(paddocksProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Standings')),
      body: paddocksAsync.when(
        data: (paddocks) {
          if (paddocks.isNotEmpty && _selectedPaddockId == null) {
            _selectedPaddockId = paddocks.first.id;
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              DropdownButtonFormField<int>(
                value: _selectedPaddockId,
                decoration: const InputDecoration(labelText: 'Paddock'),
                items: paddocks
                    .map(
                      (paddock) => DropdownMenuItem(
                        value: paddock.id,
                        child: Text(paddock.name),
                      ),
                    )
                    .toList(),
                onChanged: (value) => setState(() => _selectedPaddockId = value),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<int>(
                value: _seasonId,
                decoration: const InputDecoration(labelText: 'Saison'),
                items: const [
                  DropdownMenuItem(value: 2026, child: Text('2026')),
                ],
                onChanged: (value) => setState(() => _seasonId = value ?? 2026),
              ),
              const SizedBox(height: 24),
              if (_selectedPaddockId == null)
                const Text('Sélectionnez un paddock pour voir le classement.')
              else
                _StandingsList(
                  seasonId: _seasonId,
                  paddockId: _selectedPaddockId!,
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

class _StandingsList extends ConsumerWidget {
  const _StandingsList({required this.seasonId, required this.paddockId});

  final int seasonId;
  final int paddockId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final standingsAsync = ref.watch(seasonStandingsProvider((seasonId: seasonId, paddockId: paddockId)));

    return standingsAsync.when(
      data: (standings) {
        if (standings.isEmpty) {
          return const Text('Classement indisponible pour le moment.');
        }
        return Column(
          children: standings.map((standing) => _StandingTile(standing: standing)).toList(),
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, _) => Text('Erreur: $err'),
    );
  }
}

class _StandingTile extends StatelessWidget {
  const _StandingTile({required this.standing});

  final Standing standing;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: CircleAvatar(child: Text('${standing.rank}')),
        title: Text('User #${standing.userId}'),
        trailing: Text(standing.points.toStringAsFixed(1)),
      ),
    );
  }
}
