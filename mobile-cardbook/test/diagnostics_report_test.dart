import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_cardbook/features/diagnostics/data/diagnostics_repository.dart';

void main() {
  test('DiagnosticsReport summarizes check states', () {
    final report = DiagnosticsReport(
      generatedAt: DateTime(2026, 7, 20),
      appVersionName: '0.1.3',
      appVersionCode: 4,
      packageName: 'com.cardbook.app',
      apiBaseUrl: 'https://example.test/api/v1',
      publicBaseUrl: 'https://example.test',
      hasAccessToken: true,
      hasRefreshToken: false,
      checks: const [
        DiagnosticCheck.ok(
          title: 'Health',
          target: '/health/',
          message: 'ok',
        ),
        DiagnosticCheck(
          title: 'Sesion',
          target: '/accounts/me/',
          message: 'sin token',
          state: DiagnosticState.warning,
        ),
        DiagnosticCheck.fail(
          title: 'APK',
          target: '/android/version/',
          message: 'fallo',
        ),
      ],
    );

    expect(report.okCount, 1);
    expect(report.warningCount, 1);
    expect(report.failCount, 1);
    expect(report.isHealthy, isFalse);
  });
}
