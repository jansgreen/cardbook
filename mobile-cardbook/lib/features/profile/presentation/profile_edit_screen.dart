import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/profile/data/profile_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class ProfileEditScreen extends ConsumerStatefulWidget {
  const ProfileEditScreen({this.profile, super.key});

  final Map<String, dynamic>? profile;

  @override
  ConsumerState<ProfileEditScreen> createState() => _ProfileEditScreenState();
}

class _ProfileEditScreenState extends ConsumerState<ProfileEditScreen> {
  late final TextEditingController _firstName;
  late final TextEditingController _lastName;
  late final TextEditingController _email;
  late final TextEditingController _phone;
  String _language = 'es';
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    final profile = widget.profile ?? const <String, dynamic>{};
    _firstName = TextEditingController(text: _text(profile['first_name']));
    _lastName = TextEditingController(text: _text(profile['last_name']));
    _email = TextEditingController(text: _text(profile['email']));
    _phone = TextEditingController(text: _text(profile['phone_number']));
    _language = _text(profile['preferred_language'], fallback: 'es');
  }

  @override
  void dispose() {
    _firstName.dispose();
    _lastName.dispose();
    _email.dispose();
    _phone.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await ref.read(profileRepositoryProvider).update({
        'first_name': _firstName.text.trim(),
        'last_name': _lastName.text.trim(),
        'email': _email.text.trim(),
        'phone_number': _phone.text.trim(),
        'preferred_language': _language,
      });
      ref.invalidate(profileProvider);
      if (mounted) context.pop();
    } catch (_) {
      if (mounted) setState(() => _error = 'No pudimos actualizar tu perfil.');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
            children: [
              Row(
                children: [
                  IconButton(
                    onPressed: _saving ? null : () => context.pop(),
                    icon: const Icon(Icons.arrow_back_rounded),
                  ),
                  const Spacer(),
                ],
              ),
              const SizedBox(height: 12),
              GlassCard(
                padding: const EdgeInsets.all(20),
                gradient: AppGradients.cardGlow,
                child: const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    StatusBadge(label: 'Perfil', icon: Icons.person_rounded, color: AppColors.gold),
                    SizedBox(height: 18),
                    Text('Editar perfil', style: TextStyle(fontSize: 30, height: 1.05, fontWeight: FontWeight.w900)),
                    SizedBox(height: 8),
                    Text('Actualiza tus datos basicos de Cardbook.', style: TextStyle(color: AppColors.muted, height: 1.45)),
                  ],
                ),
              ),
              const SizedBox(height: 18),
              GlassCard(
                child: Column(
                  children: [
                    _Field(controller: _firstName, label: 'Nombre'),
                    _Field(controller: _lastName, label: 'Apellido'),
                    _Field(controller: _email, label: 'Email', keyboardType: TextInputType.emailAddress),
                    _Field(controller: _phone, label: 'Telefono', keyboardType: TextInputType.phone),
                    DropdownButtonFormField<String>(
                      value: _language,
                      items: const [
                        DropdownMenuItem(value: 'es', child: Text('Espanol')),
                        DropdownMenuItem(value: 'en', child: Text('English')),
                        DropdownMenuItem(value: 'fr', child: Text('Francais')),
                        DropdownMenuItem(value: 'pt', child: Text('Portugues')),
                      ],
                      onChanged: _saving ? null : (value) => setState(() => _language = value ?? 'es'),
                      decoration: const InputDecoration(labelText: 'Idioma preferido'),
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: 12),
                      Text(_error!, style: const TextStyle(color: Colors.redAccent)),
                    ],
                    const SizedBox(height: 18),
                    FilledButton.icon(
                      onPressed: _saving ? null : _submit,
                      icon: _saving
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                            )
                          : const Icon(Icons.save_rounded),
                      label: Text(_saving ? 'Guardando...' : 'Guardar perfil'),
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

class _Field extends StatelessWidget {
  const _Field({
    required this.controller,
    required this.label,
    this.keyboardType,
  });

  final TextEditingController controller;
  final String label;
  final TextInputType? keyboardType;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: TextFormField(
        controller: controller,
        keyboardType: keyboardType,
        decoration: InputDecoration(labelText: label),
      ),
    );
  }
}

String _text(dynamic value, {String fallback = ''}) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
}
