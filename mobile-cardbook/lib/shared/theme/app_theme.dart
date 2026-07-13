import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppColors {
  static const ink = Color(0xFF061322);
  static const inkAlt = Color(0xFF091A2C);
  static const panel = Color(0xFF0B1B2D);
  static const panelSoft = Color(0xFF102843);
  static const panelHigh = Color(0xFF162F4F);
  static const blue = Color(0xFF1E63FF);
  static const purple = Color(0xFF7B4DFF);
  static const violet = Color(0xFF925CFF);
  static const cyan = Color(0xFF16C7F5);
  static const gold = Color(0xFFFFC247);
  static const green = Color(0xFF20D17D);
  static const red = Color(0xFFFF4D6D);
  static const text = Color(0xFFF8FBFF);
  static const muted = Color(0xFF9AA9BD);
  static const stroke = Color(0xFF243A55);
}

class AppRadius {
  static const sm = 12.0;
  static const md = 18.0;
  static const lg = 24.0;
  static const xl = 32.0;
}

class AppSpacing {
  static const xs = 6.0;
  static const sm = 10.0;
  static const md = 16.0;
  static const lg = 22.0;
  static const xl = 30.0;
}

class AppGradients {
  static const page = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF151B68), Color(0xFF07192C), Color(0xFF061322)],
    stops: [0, .46, 1],
  );

  static const primary = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [AppColors.purple, AppColors.blue],
  );

  static const cardGlow = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0x332F6BFF), Color(0x11000000)],
  );
}

class AppTheme {
  static ThemeData dark() {
    final textTheme = GoogleFonts.interTextTheme(ThemeData.dark().textTheme);
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: AppColors.ink,
      colorScheme: const ColorScheme.dark(
        primary: AppColors.purple,
        secondary: AppColors.blue,
        tertiary: AppColors.gold,
        surface: AppColors.panel,
      ),
      textTheme: textTheme.apply(
        bodyColor: AppColors.text,
        displayColor: AppColors.text,
      ),
      cardTheme: CardThemeData(
        color: AppColors.panel,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.md),
          side: const BorderSide(color: AppColors.stroke),
        ),
      ),
      appBarTheme: const AppBarTheme(
        elevation: 0,
        centerTitle: false,
        backgroundColor: Colors.transparent,
        foregroundColor: AppColors.text,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.purple,
          foregroundColor: Colors.white,
          minimumSize: const Size.fromHeight(52),
          shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppRadius.md)),
          textStyle: const TextStyle(fontWeight: FontWeight.w800),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.panelSoft,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.stroke),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.stroke),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.purple, width: 1.5),
        ),
      ),
    );
  }
}
