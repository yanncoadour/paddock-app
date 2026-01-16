import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'core/theme.dart';
import 'presentation/navigation/app_router.dart';

class PaddockApp extends ConsumerWidget {
  const PaddockApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);

    return MaterialApp.router(
      title: 'Paddock',
      theme: buildDarkTheme(),
      routerConfig: router,
    );
  }
}
