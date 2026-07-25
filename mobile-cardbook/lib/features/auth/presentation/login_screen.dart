import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/auth/data/session_controller.dart';
import 'package:mobile_cardbook/features/push/data/push_notification_service.dart';
import 'package:mobile_cardbook/shared/navigation/mobile_navigation.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _username = TextEditingController();
  final _password = TextEditingController();
  bool _loading = false;
  bool _checkingSession = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    Future.microtask(_restoreSession);
  }

  @override
  void dispose() {
    _username.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _restoreSession() async {
    final bootstrap = await ref.read(sessionControllerProvider.future);
    if (!mounted) return;
    if (bootstrap != null) {
      await ref.read(pushNotificationControllerProvider).registerDevice();
      if (!mounted) return;
      context.go(defaultMobileRoute(bootstrap));
      return;
    }
    setState(() => _checkingSession = false);
  }

  Future<void> _submit() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final bootstrap =
          await ref.read(sessionControllerProvider.notifier).login(
                username: _username.text.trim(),
                password: _password.text,
              );
      await ref.read(pushNotificationControllerProvider).registerDevice();
      if (mounted) context.go(defaultMobileRoute(bootstrap));
    } catch (error) {
      setState(
          () => _error = 'No pudimos iniciar sesion. Revisa tus credenciales.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_checkingSession) {
      return const Scaffold(
        body: AppGradientBackground(
          child: Center(
            child: CircularProgressIndicator(
                strokeWidth: 3, color: AppColors.purple),
          ),
        ),
      );
    }

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              const SizedBox(height: 42),
              const _LoginBrand(),
              const SizedBox(height: 54),
              GlassCard(
                padding: const EdgeInsets.all(22),
                gradient: AppGradients.cardGlow,
                borderColor: AppColors.blue.withValues(alpha: .28),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const StatusBadge(
                        label: 'Acceso seguro',
                        icon: Icons.lock_rounded,
                        color: AppColors.gold),
                    const SizedBox(height: 18),
                    const Text(
                      'Bienvenido de vuelta',
                      style: TextStyle(
                          fontSize: 40,
                          height: 1.05,
                          fontWeight: FontWeight.w900),
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      'Administra empresas, tarjetas digitales, alianzas y Book desde una experiencia movil nativa.',
                      style: TextStyle(
                          color: AppColors.muted, fontSize: 16, height: 1.5),
                    ),
                    const SizedBox(height: 28),
                    TextField(
                        controller: _username,
                        decoration:
                            const InputDecoration(labelText: 'Usuario')),
                    const SizedBox(height: 14),
                    TextField(
                      controller: _password,
                      obscureText: true,
                      decoration:
                          const InputDecoration(labelText: 'Contrasena'),
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: 12),
                      Text(_error!,
                          style: const TextStyle(color: Colors.redAccent)),
                    ],
                    const SizedBox(height: 22),
                    FilledButton.icon(
                      onPressed: _loading ? null : _submit,
                      icon: _loading
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2, color: Colors.white),
                            )
                          : const Icon(Icons.arrow_forward_rounded),
                      label:
                          Text(_loading ? 'Entrando...' : 'Entrar a Cardbook'),
                    ),
                    const SizedBox(height: 12),
                    Center(
                      child: TextButton(
                        onPressed:
                            _loading ? null : () => context.go('/register'),
                        child: const Text('Crear cuenta nueva'),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _LoginBrand extends StatelessWidget {
  const _LoginBrand();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 56,
          height: 56,
          clipBehavior: Clip.antiAlias,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            color: Colors.white,
            boxShadow: [
              BoxShadow(
                color: AppColors.purple.withValues(alpha: .28),
                blurRadius: 22,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: Image.asset('assets/images/logo.png', fit: BoxFit.cover),
        ),
        const SizedBox(width: 12),
        const Text('cardbook',
            style: TextStyle(fontSize: 28, fontWeight: FontWeight.w900)),
      ],
    );
  }
}
