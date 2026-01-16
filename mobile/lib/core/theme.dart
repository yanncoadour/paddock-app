import 'package:flutter/material.dart';

ThemeData buildDarkTheme() {
  final base = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    colorSchemeSeed: const Color(0xFF00D1B2),
  );

  return base.copyWith(
    scaffoldBackgroundColor: const Color(0xFF0D0F12),
    cardTheme: const CardThemeData(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      elevation: 1,
    ),
    appBarTheme: const AppBarTheme(
      centerTitle: false,
      backgroundColor: Color(0xFF0D0F12),
      foregroundColor: Colors.white,
    ),
  );
}
