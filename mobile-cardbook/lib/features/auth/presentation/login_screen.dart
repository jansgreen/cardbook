import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/auth/data/auth_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _username = TextEditingController();
  final _password = TextEditingController();
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _username.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ref.read(authRepositoryProvider).login(
            username: _username.text.trim(),
            password: _password.text,
          );
      if (mounted) context.go('/');
    } catch (error) {
      setState(() => _error = 'No pudimos iniciar sesion. Revisa tus credenciales.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              const SizedBox(height: 42),
              Row(
                children: [
                  Container(
                    width: 54,
                    height: 54,
                    clipBehavior: Clip.antiAlias,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(16),
                      color: Colors.white,
                    ),
                    child: Image.asset('assets/images/logo.png', fit: BoxFit.cover),
                  ),
                  const SizedBox(width: 12),
                  const Text('cardbook', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w900)),
                ],
              ),
              const SizedBox(height: 54),
              const Text('Acceso seguro', style: TextStyle(color: AppColors.gold, fontWeight: FontWeight.w900)),
              const SizedBox(height: 12),
              const Text(
                'Bienvenido de vuelta',
                style: TextStyle(fontSize: 42, height: 1.05, fontWeight: FontWeight.w900),
              ),
              const SizedBox(height: 12),
              const Text(
                'Administra empresas, tarjetas digitales, alianzas y Book desde una experiencia movil nativa.',
                style: TextStyle(color: AppColors.muted, fontSize: 16, height: 1.5),
              ),
              const SizedBox(height: 34),
              TextField(controller: _username, decoration: const InputDecoration(labelText: 'Usuario')),
              const SizedBox(height: 14),
              TextField(
                controller: _password,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'Contrasena'),
              ),
              if (_error != null) ...[
                const SizedBox(height: 12),
                Text(_error!, style: const TextStyle(color: Colors.redAccent)),
              ],
              const SizedBox(height: 22),
              FilledButton(
                onPressed: _loading ? null : _submit,
                style: FilledButton.styleFrom(
                  minimumSize: const Size.fromHeight(54),
                  backgroundColor: AppColors.purple,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                ),
                child: Text(_loading ? 'Entrando...' : 'Entrar a Cardbook'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
