import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/auth/data/auth_repository.dart';
import 'package:mobile_cardbook/features/auth/data/session_controller.dart';
import 'package:mobile_cardbook/shared/navigation/mobile_navigation.dart';
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
  final _referralCode = TextEditingController();
  final _phone = TextEditingController();
  final _city = TextEditingController();
  final _experience = TextEditingController();
  final _agentReason = TextEditingController();
  String _intent = 'company';
  bool _agentHasCode = true;
  bool _applicationSubmitted = false;
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
    _referralCode.dispose();
    _phone.dispose();
    _city.dispose();
    _experience.dispose();
    _agentReason.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      if (_intent == 'agent' && !_agentHasCode && !_applicationSubmitted) {
        final fullName = [_firstName.text.trim(), _lastName.text.trim()]
            .where((value) => value.isNotEmpty)
            .join(' ');
        await ref.read(authRepositoryProvider).applyAsAgent(
              fullName: fullName.isEmpty ? _username.text.trim() : fullName,
              email: _email.text.trim(),
              phoneNumber: _phone.text.trim(),
              city: _city.text.trim(),
              experience: _experience.text.trim(),
              reason: _agentReason.text.trim(),
            );
        _applicationSubmitted = true;
      }

      final bootstrap =
          await ref.read(sessionControllerProvider.notifier).register(
                username: _username.text.trim(),
                email: _email.text.trim(),
                password: _password.text,
                passwordConfirm: _passwordConfirm.text,
                registrationIntent: _intent,
                firstName: _firstName.text.trim(),
                lastName: _lastName.text.trim(),
                referralCode: _intent == 'agent' && _agentHasCode
                    ? _referralCode.text.trim()
                    : '',
              );
      if (mounted) context.go(defaultMobileRoute(bootstrap));
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
                        'Dinos como usaras Cardbook para preparar tu cuenta y mostrarte solo las herramientas correctas.',
                        style: TextStyle(
                            color: AppColors.muted, fontSize: 16, height: 1.45),
                      ),
                      const SizedBox(height: 24),
                      _IntentSelector(
                        value: _intent,
                        onChanged: _loading
                            ? null
                            : (value) => setState(() {
                                  _intent = value;
                                  _error = null;
                                }),
                      ),
                      const SizedBox(height: 20),
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
                      if (_intent == 'agent') ...[
                        const SizedBox(height: 4),
                        _AgentModeToggle(
                          hasCode: _agentHasCode,
                          onChanged: _loading
                              ? null
                              : (value) => setState(() {
                                    _agentHasCode = value;
                                    _applicationSubmitted = false;
                                    _error = null;
                                  }),
                        ),
                        const SizedBox(height: 14),
                        if (_agentHasCode)
                          _Field(
                            controller: _referralCode,
                            label: 'Codigo de referido',
                            required: true,
                          )
                        else ...[
                          _Field(
                              controller: _phone,
                              label: 'Telefono',
                              keyboardType: TextInputType.phone),
                          _Field(controller: _city, label: 'Ciudad'),
                          _Field(
                            controller: _experience,
                            label: 'Experiencia como agente',
                            maxLines: 3,
                          ),
                          _Field(
                            controller: _agentReason,
                            label: 'Por que quieres ser agente',
                            required: true,
                            maxLines: 4,
                          ),
                        ],
                      ],
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
                        label: Text(_loading
                            ? 'Creando...'
                            : _intent == 'agent' && !_agentHasCode
                                ? 'Aplicar y crear cuenta'
                                : 'Crear cuenta'),
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
    this.maxLines = 1,
  });

  final TextEditingController controller;
  final String label;
  final bool required;
  final bool obscureText;
  final TextInputType? keyboardType;
  final int maxLines;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: TextFormField(
        controller: controller,
        obscureText: obscureText,
        keyboardType: keyboardType,
        maxLines: obscureText ? 1 : maxLines,
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

class _IntentSelector extends StatelessWidget {
  const _IntentSelector({
    required this.value,
    required this.onChanged,
  });

  final String value;
  final ValueChanged<String>? onChanged;

  @override
  Widget build(BuildContext context) {
    final items = [
      _IntentOption(
        keyName: 'company',
        title: 'Para mi empresa',
        subtitle: 'Empresas, perfiles, tarjetas, websites y alianzas.',
        icon: Icons.business_center_rounded,
      ),
      _IntentOption(
        keyName: 'job',
        title: 'Para buscar trabajo',
        subtitle: 'White Card Job, empresas, notificaciones y Book.',
        icon: Icons.work_rounded,
      ),
      _IntentOption(
        keyName: 'agent',
        title: 'Agente Cardbook',
        subtitle: 'Referidos, ventas, empresas y tarjetas para clientes.',
        icon: Icons.handshake_rounded,
      ),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Para que usaras Cardbook?',
            style: TextStyle(fontWeight: FontWeight.w900)),
        const SizedBox(height: 10),
        for (final item in items) ...[
          _IntentTile(
            option: item,
            selected: value == item.keyName,
            onTap: onChanged == null ? null : () => onChanged!(item.keyName),
          ),
          const SizedBox(height: 10),
        ],
      ],
    );
  }
}

class _IntentOption {
  const _IntentOption({
    required this.keyName,
    required this.title,
    required this.subtitle,
    required this.icon,
  });

  final String keyName;
  final String title;
  final String subtitle;
  final IconData icon;
}

class _IntentTile extends StatelessWidget {
  const _IntentTile({
    required this.option,
    required this.selected,
    required this.onTap,
  });

  final _IntentOption option;
  final bool selected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppRadius.md),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: selected
              ? AppColors.purple.withValues(alpha: .18)
              : AppColors.inkAlt.withValues(alpha: .62),
          borderRadius: BorderRadius.circular(AppRadius.md),
          border: Border.all(
            color: selected ? AppColors.purple : AppColors.stroke,
          ),
        ),
        child: Row(
          children: [
            Icon(option.icon,
                color: selected ? AppColors.purple : AppColors.muted),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(option.title,
                      style: const TextStyle(fontWeight: FontWeight.w900)),
                  const SizedBox(height: 3),
                  Text(option.subtitle,
                      style:
                          const TextStyle(color: AppColors.muted, height: 1.3)),
                ],
              ),
            ),
            Icon(
              selected
                  ? Icons.radio_button_checked_rounded
                  : Icons.radio_button_off_rounded,
              color: selected ? AppColors.purple : AppColors.muted,
            ),
          ],
        ),
      ),
    );
  }
}

class _AgentModeToggle extends StatelessWidget {
  const _AgentModeToggle({
    required this.hasCode,
    required this.onChanged,
  });

  final bool hasCode;
  final ValueChanged<bool>? onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(5),
      decoration: BoxDecoration(
        color: AppColors.inkAlt.withValues(alpha: .72),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.stroke),
      ),
      child: Row(
        children: [
          Expanded(
            child: _AgentModeButton(
              label: 'Tengo codigo',
              selected: hasCode,
              onTap: onChanged == null ? null : () => onChanged!(true),
            ),
          ),
          Expanded(
            child: _AgentModeButton(
              label: 'Quiero aplicar',
              selected: !hasCode,
              onTap: onChanged == null ? null : () => onChanged!(false),
            ),
          ),
        ],
      ),
    );
  }
}

class _AgentModeButton extends StatelessWidget {
  const _AgentModeButton({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppRadius.sm),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(vertical: 11),
        decoration: BoxDecoration(
          color: selected ? AppColors.purple : Colors.transparent,
          borderRadius: BorderRadius.circular(AppRadius.sm),
        ),
        alignment: Alignment.center,
        child: Text(
          label,
          style: TextStyle(
            color: selected ? Colors.white : AppColors.muted,
            fontWeight: FontWeight.w900,
          ),
        ),
      ),
    );
  }
}
