import 'package:flutter/material.dart';

void main() {
  runApp(const PaddockApp());
}

class PaddockApp extends StatelessWidget {
  const PaddockApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Paddock',
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
      ),
      home: const MainShell(),
    );
  }
}

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _currentIndex = 0;

  static const List<_TabInfo> _tabs = [
    _TabInfo(label: 'Paddock'),
    _TabInfo(label: 'GP'),
    _TabInfo(label: 'Standings'),
    _TabInfo(label: 'Profile'),
  ];

  @override
  Widget build(BuildContext context) {
    final currentTab = _tabs[_currentIndex];

    return Scaffold(
      appBar: AppBar(
        title: Text(currentTab.label),
      ),
      body: Center(
        child: Text(
          currentTab.label,
          style: Theme.of(context).textTheme.headlineMedium,
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.group_outlined),
            label: 'Paddock',
          ),
          NavigationDestination(
            icon: Icon(Icons.flag_outlined),
            label: 'GP',
          ),
          NavigationDestination(
            icon: Icon(Icons.emoji_events_outlined),
            label: 'Standings',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            label: 'Profile',
          ),
        ],
      ),
    );
  }
}

class _TabInfo {
  final String label;

  const _TabInfo({required this.label});
}
