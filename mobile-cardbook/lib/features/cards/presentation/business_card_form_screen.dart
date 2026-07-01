import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/cards/data/cards_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class BusinessCardFormScreen extends ConsumerStatefulWidget {
  const BusinessCardFormScreen({this.card, super.key});

  final Map<String, dynamic>? card;

  @override
  ConsumerState<BusinessCardFormScreen> createState() => _BusinessCardFormScreenState();
}

class _BusinessCardFormScreenState extends ConsumerState<BusinessCardFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _displayName;
  late final TextEditingController _jobTitle;
  late final TextEditingController _companyName;
  late final TextEditingController _phone;
  late final TextEditingController _email;
  late final TextEditingController _website;
  late final TextEditingController _address;
  late final TextEditingController _tagline;
  late final TextEditingController _services;
  int? _profileId;
  bool _saving = false;
  String? _error;

  bool get _isEditing => widget.card != null;

  @override
  void initState() {
    super.initState();
    final card = widget.card ?? const <String, dynamic>{};
    _profileId = _intValue(card['profile']);
    _displayName = TextEditingController(text: _text(card['display_name']));
    _jobTitle = TextEditingController(text: _text(card['job_title']));
    _companyName = TextEditingController(text: _text(card['company_name']));
    _phone = TextEditingController(text: _text(card['phone_number']));
    _email = TextEditingController(text: _text(card['email']));
    _website = TextEditingController(text: _text(card['website']));
    _address = TextEditingController(text: _text(card['address']));
    _tagline = TextEditingController(text: _text(card['tagline']));
    _services = TextEditingController(text: _text(card['services']));
  }

  @override
  void dispose() {
    _displayName.dispose();
    _jobTitle.dispose();
    _companyName.dispose();
    _phone.dispose();
    _email.dispose();
    _website.dispose();
    _address.dispose();
    _tagline.dispose();
    _services.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_profileId == null) {
      setState(() => _error = 'Selecciona un perfil de negocio.');
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });

    final payload = {
      'profile': _profileId,
      'display_name': _displayName.text.trim(),
      'job_title': _jobTitle.text.trim(),
      'company_name': _companyName.text.trim(),
      'phone_number': _phone.text.trim(),
      'email': _email.text.trim(),
      'website': _url(_website.text),
      'address': _address.text.trim(),
      'tagline': _tagline.text.trim(),
      'services': _services.text.trim(),
    };

    try {
      final repository = ref.read(cardRepositoryProvider);
      if (_isEditing) {
        final id = widget.card?['id'];
        if (id is! int) throw StateError('Tarjeta invalida.');
        await repository.updateBusiness(id, payload);
      } else {
        await repository.createBusiness(payload);
      }
      ref.invalidate(businessCardsProvider);
      if (mounted) context.pop();
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'No pudimos guardar la tarjeta. Revisa los datos e intenta otra vez.');
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final profiles = ref.watch(digitalCardsProvider);

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: Form(
            key: _formKey,
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
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      StatusBadge(
                        label: _isEditing ? 'Editar presentacion' : 'Nueva presentacion',
                        icon: Icons.contact_page_rounded,
                        color: AppColors.gold,
                      ),
                      const SizedBox(height: 18),
                      Text(
                        _isEditing ? 'Actualizar tarjeta' : 'Crear tarjeta de presentacion',
                        style: const TextStyle(fontSize: 30, height: 1.05, fontWeight: FontWeight.w900),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Crea una tarjeta de negocio lista para compartir e imprimir.',
                        style: TextStyle(color: AppColors.muted, height: 1.45),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                GlassCard(
                  child: profiles.when(
                    loading: () => const SizedBox(height: 120, child: AsyncStateView.loading()),
                    error: (_, __) => const AsyncStateView.error('No pudimos cargar tus perfiles.'),
                    data: (items) => Column(
                      children: [
                        DropdownButtonFormField<int>(
                          value: _profileId,
                          items: [
                            for (final profile in items)
                              DropdownMenuItem<int>(
                                value: _intValue(profile['id']),
                                child: Text(_profileLabel(profile)),
                              ),
                          ],
                          onChanged: _saving ? null : (value) => setState(() => _profileId = value),
                          validator: (value) => value == null ? 'Selecciona un perfil.' : null,
                          decoration: const InputDecoration(labelText: 'Perfil de negocio'),
                        ),
                        const SizedBox(height: 14),
                        _Field(controller: _displayName, label: 'Nombre visible', isRequired: true),
                        _Field(controller: _jobTitle, label: 'Cargo'),
                        _Field(controller: _companyName, label: 'Empresa', isRequired: true),
                        _Field(controller: _phone, label: 'Telefono', keyboardType: TextInputType.phone),
                        _Field(controller: _email, label: 'Email', keyboardType: TextInputType.emailAddress),
                        _Field(controller: _website, label: 'Website', keyboardType: TextInputType.url),
                        _Field(controller: _address, label: 'Direccion', maxLines: 2),
                        _Field(controller: _tagline, label: 'Frase corta'),
                        _Field(controller: _services, label: 'Servicios', maxLines: 3),
                        if (_error != null) ...[
                          const SizedBox(height: 8),
                          Text(_error!, style: const TextStyle(color: Colors.redAccent)),
                        ],
                        const SizedBox(height: 16),
                        FilledButton.icon(
                          onPressed: _saving ? null : _submit,
                          icon: _saving
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                )
                              : const Icon(Icons.save_rounded),
                          label: Text(_saving ? 'Guardando...' : 'Guardar tarjeta'),
                        ),
                      ],
                    ),
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
    this.isRequired = false,
    this.maxLines = 1,
    this.keyboardType,
  });

  final TextEditingController controller;
  final String label;
  final bool isRequired;
  final int maxLines;
  final TextInputType? keyboardType;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: TextFormField(
        controller: controller,
        maxLines: maxLines,
        keyboardType: keyboardType,
        validator: isRequired
            ? (value) {
                if (value == null || value.trim().isEmpty) return 'Este campo es obligatorio.';
                return null;
              }
            : null,
        decoration: InputDecoration(labelText: label),
      ),
    );
  }
}

String _profileLabel(Map<String, dynamic> profile) {
  final job = _text(profile['job_title']);
  final email = _text(profile['email']);
  if (job.isNotEmpty && email.isNotEmpty) return '$job - $email';
  if (job.isNotEmpty) return job;
  if (email.isNotEmpty) return email;
  return 'Perfil ${profile['id']}';
}

String _text(dynamic value) => value?.toString().trim() ?? '';

int? _intValue(dynamic value) {
  if (value is int) return value;
  return int.tryParse(value?.toString() ?? '');
}

String _url(String value) {
  final text = value.trim();
  if (text.isEmpty) return '';
  return text.startsWith('http://') || text.startsWith('https://') ? text : 'https://$text';
}
