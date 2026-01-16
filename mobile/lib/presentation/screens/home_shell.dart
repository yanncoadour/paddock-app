import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key, required this.child});

  final Widget child;

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _indexForLocation(String location) {
    if (location.startsWith('/paddocks')) return 0;
    if (location.startsWith('/gps')) return 1;
    if (location.startsWith('/standings')) return 2;
    if (location.startsWith('/profile')) return 3;
    return 0;
  }

  void _onTap(int index) {
    switch (index) {
      case 0:
        context.go('/paddocks');
        break;
      case 1:
        context.go('/gps');
        break;
      case 2:
        context.go('/standings');
        break;
      case 3:
        context.go('/profile');
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).uri.toString();
    final currentIndex = _indexForLocation(location);

    return Scaffold(
      body: widget.child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex,
        onDestinationSelected: _onTap,
        destinations: const [
          NavigationDestination(icon: Icon(Icons.group_outlined), label: 'Paddock'),
          NavigationDestination(icon: Icon(Icons.flag_outlined), label: 'GP'),
          NavigationDestination(icon: Icon(Icons.emoji_events_outlined), label: 'Standings'),
          NavigationDestination(icon: Icon(Icons.person_outline), label: 'Profile'),
        ],
      ),
    );
  }
}
