import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/features/auth/data/auth_repository.dart';
import 'package:mobile_cardbook/features/home/data/mobile_bootstrap_repository.dart';

final sessionControllerProvider =
    AsyncNotifierProvider<SessionController, CardbookBootstrap?>(
  SessionController.new,
);

class SessionController extends AsyncNotifier<CardbookBootstrap?> {
  @override
  Future<CardbookBootstrap?> build() async {
    final auth = ref.read(authRepositoryProvider);
    if (!await auth.hasStoredSession()) return null;
    try {
      return await ref.read(mobileBootstrapRepositoryProvider).fetch();
    } catch (_) {
      await auth.logout();
      return null;
    }
  }

  Future<CardbookBootstrap> login({
    required String username,
    required String password,
  }) async {
    state = const AsyncLoading();
    try {
      await ref.read(authRepositoryProvider).login(
            username: username,
            password: password,
          );
      final bootstrap =
          await ref.read(mobileBootstrapRepositoryProvider).fetch();
      state = AsyncData(bootstrap);
      ref.invalidate(mobileBootstrapProvider);
      return bootstrap;
    } catch (error, stackTrace) {
      state = AsyncError(error, stackTrace);
      rethrow;
    }
  }

  Future<CardbookBootstrap> register({
    required String username,
    required String email,
    required String password,
    required String passwordConfirm,
    required String registrationIntent,
    String firstName = '',
    String lastName = '',
    String referralCode = '',
  }) async {
    state = const AsyncLoading();
    try {
      await ref.read(authRepositoryProvider).register(
            username: username,
            email: email,
            password: password,
            passwordConfirm: passwordConfirm,
            registrationIntent: registrationIntent,
            firstName: firstName,
            lastName: lastName,
            referralCode: referralCode,
          );
      final bootstrap =
          await ref.read(mobileBootstrapRepositoryProvider).fetch();
      state = AsyncData(bootstrap);
      ref.invalidate(mobileBootstrapProvider);
      return bootstrap;
    } catch (error, stackTrace) {
      state = AsyncError(error, stackTrace);
      rethrow;
    }
  }

  Future<void> logout() async {
    await ref.read(authRepositoryProvider).logout();
    ref.invalidate(mobileBootstrapProvider);
    state = const AsyncData(null);
  }
}
