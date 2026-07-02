import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/app/cardbook_app.dart';

void main() {
  testWidgets('Cardbook app builds', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: CardbookApp()));
    expect(find.byType(CardbookApp), findsOneWidget);
  });
}
