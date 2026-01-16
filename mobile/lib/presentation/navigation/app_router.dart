import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:paddock/presentation/providers.dart';
import 'package:paddock/presentation/screens/auth/login_screen.dart';
import 'package:paddock/presentation/screens/auth/register_screen.dart';
import 'package:paddock/presentation/screens/gps/gp_detail_screen.dart';
import 'package:paddock/presentation/screens/gps/gps_screen.dart';
import 'package:paddock/presentation/screens/home_shell.dart';
import 'package:paddock/presentation/screens/paddocks/paddock_detail_screen.dart';
import 'package:paddock/presentation/screens/paddocks/paddocks_screen.dart';
import 'package:paddock/presentation/screens/profile/profile_screen.dart';
import 'package:paddock/presentation/screens/profile/settings_screen.dart';
import 'package:paddock/presentation/screens/splash_screen.dart';
import 'package:paddock/presentation/screens/standings/standings_screen.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authStateProvider);

  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: GoRouterRefreshStream(ref.watch(authStateStreamProvider)),
    redirect: (context, state) {
      final isLoggingIn = state.matchedLocation == '/login' || state.matchedLocation == '/register';
      final isSplash = state.matchedLocation == '/splash';
      final user = authState.valueOrNull;

      if (authState.isLoading && !isSplash) {
        return '/splash';
      }

      if (user == null && !isLoggingIn) {
        return '/login';
      }

      if (user != null && (isLoggingIn || isSplash)) {
        return '/paddocks';
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      ShellRoute(
        builder: (context, state, child) => HomeShell(child: child),
        routes: [
          GoRoute(
            path: '/paddocks',
            builder: (context, state) => const PaddocksScreen(),
          ),
          GoRoute(
            path: '/paddocks/:id',
            builder: (context, state) => PaddockDetailScreen(
              paddockId: int.parse(state.pathParameters['id']!),
            ),
          ),
          GoRoute(
            path: '/gps',
            builder: (context, state) => const GpsScreen(),
          ),
          GoRoute(
            path: '/gps/:id',
            builder: (context, state) => GpDetailScreen(
              gpId: int.parse(state.pathParameters['id']!),
            ),
          ),
          GoRoute(
            path: '/standings',
            builder: (context, state) => const StandingsScreen(),
          ),
          GoRoute(
            path: '/profile',
            builder: (context, state) => const ProfileScreen(),
          ),
          GoRoute(
            path: '/settings',
            builder: (context, state) => const SettingsScreen(),
          ),
        ],
      ),
    ],
  );
});

class GoRouterRefreshStream extends ChangeNotifier {
  GoRouterRefreshStream(Stream<dynamic> stream) {
    notifyListeners();
    _subscription = stream.asBroadcastStream().listen((_) => notifyListeners());
  }

  late final StreamSubscription<dynamic> _subscription;

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}
