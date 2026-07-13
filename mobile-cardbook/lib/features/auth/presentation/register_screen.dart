import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/auth/data/auth_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _firstName = TextEditingController();
  final _lastName = TextEditingController();
  final _username = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _passwordConfirm = TextEditingController();
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _firstName.dispose();
    _lastName.dispose();
    _username.dispose();
    _email.dispose();
    _password.dispose();
    _passwordConfirm.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ref.read(authRepositoryProvider).register(
            username: _username.text.trim(),
            email: _email.text.trim(),
            password: _password.text,
            passwordConfirm: _passwordConfirm.text,
            firstName: _firstName.text.trim(),
            lastName: _lastName.text.trim(),
          );
      if (mounted) context.go('/');
    } catch (_) {
      if (mounted) {
        setState(() => _error =
            'No pudimos crear la cuenta. Revisa los datos e intenta otra vez.');
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: Form(
            key: _formKey,
            child: ListView(
              padding: const EdgeInsets.all(24),
              children: [
                Row(
                  children: [
                    IconButton(
                        onPressed: _loading ? null : () => context.go('/login'),
                        icon: const Icon(Icons.arrow_back_rounded)),
                    const Spacer(),
                  ],
                ),
                const SizedBox(height: 18),
                GlassCard(
                  padding: const EdgeInsets.all(22),
                  gradient: AppGradients.cardGlow,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const StatusBadge(
                          label: 'Nueva cuenta',
                          icon: Icons.person_add_alt_1_rounded,
                          color: AppColors.gold),
                      const SizedBox(height: 18),
                      const Text(
                        'Crear cuenta',
                        style: TextStyle(
                            fontSize: 38,
                            height: 1.05,
                            fontWeight: FontWeight.w900),
                      ),
                      const SizedBox(height: 10),
                      const Text(
                        'Registra tu usuario para crear empresas, tarjetas y guardar contactos en Book.',
                        style: TextStyle(
                            color: AppColors.muted, fontSize: 16, height: 1.45),
                      ),
                      const SizedBox(height: 24),
                      _Field(controller: _firstName, label: 'Nombre'),
                      _Field(controller: _lastName, label: 'Apellido'),
                      _Field(
                          controller: _username,
                          label: 'Usuario',
                          required: true),
                      _Field(
                          controller: _email,
                          label: 'Email',
                          required: true,
                          keyboardType: TextInputType.emailAddress),
                      _Field(
                          controller: _password,
                          label: 'Contrasena',
                          required: true,
                          obscureText: true),
                      _Field(
                          controller: _passwordConfirm,
                          label: 'Confirmar contrasena',
                          required: true,
                          obscureText: true),
                      if (_error != null) ...[
                        const SizedBox(height: 8),
                        Text(_error!,
                            style: const TextStyle(color: Colors.redAccent)),
                      ],
                      const SizedBox(height: 18),
                      FilledButton.icon(
                        onPressed: _loading ? null : _submit,
                        icon: _loading
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(
                                    strokeWidth: 2, color: Colors.white))
                            : const Icon(Icons.check_rounded),
                        label: Text(_loading ? 'Creando...' : 'Crear cuenta'),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _Field extends StatelessWidget {
  const _Field({
    required this.controller,
    required this.label,
    this.required = false,
    this.obscureText = false,
    this.keyboardType,
  });

  final TextEditingController controller;
  final String label;
  final bool required;
  final bool obscureText;
  final TextInputType? keyboardType;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: TextFormField(
        controller: controller,
        obscureText: obscureText,
        keyboardType: keyboardType,
        validator: (value) {
          if (required && (value == null || value.trim().isEmpty)) {
            return 'Este campo es obligatorio.';
          }
          if (label == 'Contrasena' && value != null && value.length < 8) {
            return 'Usa al menos 8 caracteres.';
          }
          if (label == 'Confirmar contrasena' &&
              value != null &&
              value != _passwordText(context)) {
            return 'Las contrasenas no coinciden.';
          }
          return null;
        },
        decoration: InputDecoration(labelText: label),
      ),
    );
  }

  String _passwordText(BuildContext context) {
    final state = context.findAncestorStateOfType<_RegisterScreenState>();
    return state?._password.text ?? '';
  }
}
