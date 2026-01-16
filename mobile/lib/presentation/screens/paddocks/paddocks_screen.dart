import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:paddock/presentation/providers.dart';

class PaddocksScreen extends ConsumerWidget {
  const PaddocksScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final paddocksAsync = ref.watch(paddocksProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Paddocks'),
        actions: [
          IconButton(
            onPressed: () => _showCreateDialog(context, ref),
            icon: const Icon(Icons.add),
          ),
        ],
      ),
      body: paddocksAsync.when(
        data: (paddocks) {
          if (paddocks.isEmpty) {
            return const Center(child: Text('Aucun paddock pour le moment.'));
          }
          return RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(paddocksProvider);
              await ref.read(paddocksProvider.future);
            },
            child: ListView.builder(
              itemCount: paddocks.length,
              itemBuilder: (context, index) {
                final paddock = paddocks[index];
                return Card(
                  child: ListTile(
                    title: Text(paddock.name),
                    subtitle: Text('Saison ${paddock.seasonYear} · ${paddock.status}'),
                    trailing: paddock.status == 'locked'
                        ? const Icon(Icons.lock)
                        : const Icon(Icons.lock_open),
                    onTap: () => context.go('/paddocks/${paddock.id}'),
                  ),
                );
              },
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Erreur: $err')),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showJoinDialog(context, ref),
        label: const Text('Rejoindre'),
        icon: const Icon(Icons.group_add),
      ),
    );
  }

  Future<void> _showCreateDialog(BuildContext context, WidgetRef ref) async {
    final nameController = TextEditingController();
    final seasonController = TextEditingController(text: '2026');
    final formKey = GlobalKey<FormState>();

    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Créer un paddock'),
        content: Form(
          key: formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: nameController,
                decoration: const InputDecoration(labelText: 'Nom'),
                validator: (value) => value != null && value.isNotEmpty ? null : 'Nom requis',
              ),
              TextFormField(
                controller: seasonController,
                decoration: const InputDecoration(labelText: 'Saison'),
                keyboardType: TextInputType.number,
                validator: (value) => value != null && int.tryParse(value) != null ? null : 'Année invalide',
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Annuler')),
          ElevatedButton(
            onPressed: () async {
              if (!formKey.currentState!.validate()) return;
              try {
                await ref.read(paddockRepositoryProvider).createPaddock(
                      name: nameController.text.trim(),
                      seasonYear: int.parse(seasonController.text),
                    );
                if (context.mounted) {
                  ref.invalidate(paddocksProvider);
                  Navigator.pop(context);
                }
              } catch (error) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text(error.toString())),
                  );
                }
              }
            },
            child: const Text('Créer'),
          ),
        ],
      ),
    );
  }

  Future<void> _showJoinDialog(BuildContext context, WidgetRef ref) async {
    final codeController = TextEditingController();
    final formKey = GlobalKey<FormState>();

    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Rejoindre un paddock'),
        content: Form(
          key: formKey,
          child: TextFormField(
            controller: codeController,
            decoration: const InputDecoration(labelText: 'Code invitation'),
            validator: (value) => value != null && value.isNotEmpty ? null : 'Code requis',
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Annuler')),
          ElevatedButton(
            onPressed: () async {
              if (!formKey.currentState!.validate()) return;
              try {
                await ref.read(paddockRepositoryProvider).joinPaddock(joinCode: codeController.text.trim());
                if (context.mounted) {
                  ref.invalidate(paddocksProvider);
                  Navigator.pop(context);
                }
              } catch (error) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text(error.toString())),
                  );
                }
              }
            },
            child: const Text('Rejoindre'),
          ),
        ],
      ),
    );
  }
}
