import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:paddock/core/utils/date_format.dart';
import 'package:paddock/domain/models/grand_prix.dart';
import 'package:paddock/presentation/providers.dart';

class GpsScreen extends ConsumerWidget {
  const GpsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final seasonAsync = ref.watch(currentSeasonProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Grand Prix')),
      body: seasonAsync.when(
        data: (season) {
          final gpsAsync = ref.watch(gpsProvider(season.year));
          return gpsAsync.when(
            data: (gps) => _GpsList(gps: gps),
            loading: () => const _GpsLoading(),
            error: (err, _) => _ErrorState(message: err.toString()),
          );
        },
        loading: () => const _GpsLoading(),
        error: (err, _) => _ErrorState(message: err.toString()),
      ),
    );
  }
}

class _GpsList extends ConsumerWidget {
  const _GpsList({required this.gps});

  final List<GrandPrix> gps;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (gps.isEmpty) {
      return const _EmptyState();
    }

    return RefreshIndicator(
      onRefresh: () async {
        final season = await ref.read(currentSeasonProvider.future);
        ref.invalidate(gpsProvider(season.year));
        await ref.read(gpsProvider(season.year).future);
      },
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(vertical: 8),
        itemCount: gps.length,
        itemBuilder: (context, index) {
          final gp = gps[index];
          return Card(
            child: ListTile(
              onTap: () => context.go('/gps/${gp.id}'),
              title: Text('Round ${gp.roundNumber} · ${gp.name}'),
              subtitle: Text('${gp.country} · ${formatFrenchDateTime(gp.startsAtUtc)}'),
              trailing: gp.hasSprint
                  ? const Chip(
                      label: Text('Sprint'),
                      visualDensity: VisualDensity.compact,
                    )
                  : null,
            ),
          );
        },
      ),
    );
  }
}

class _GpsLoading extends StatelessWidget {
  const _GpsLoading();

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(vertical: 8),
      itemCount: 6,
      itemBuilder: (context, index) => const Card(
        child: ListTile(
          title: SizedBox(height: 12, child: LinearProgressIndicator()),
          subtitle: SizedBox(height: 12),
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Text('Aucun Grand Prix pour le moment.'),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text('Erreur: $message'),
    );
  }
}
