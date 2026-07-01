import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/cards/data/cards_repository.dart';
import 'package:mobile_cardbook/features/companies/data/companies_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class DigitalCardFormScreen extends ConsumerStatefulWidget {
  const DigitalCardFormScreen({this.card, super.key});

  final Map<String, dynamic>? card;

  @override
  ConsumerState<DigitalCardFormScreen> createState() => _DigitalCardFormScreenState();
}

class _DigitalCardFormScreenState extends ConsumerState<DigitalCardFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _jobTitle;
  late final TextEditingController _phone;
  late final TextEditingController _email;
  late final TextEditingController _website;
  late final TextEditingController _whatsapp;
  late final TextEditingController _linkedin;
  late final TextEditingController _instagram;
  int? _companyId;
  bool _saving = false;
  String? _error;

  bool get _isEditing => widget.card != null;

  @override
  void initState() {
    super.initState();
    final card = widget.card ?? const <String, dynamic>{};
    _companyId = _intValue(card['company']);
    _jobTitle = TextEditingController(text: _text(card['job_title']));
    _phone = TextEditingController(text: _text(card['phone_number']));
    _email = TextEditingController(text: _text(card['email']));
    _website = TextEditingController(text: _text(card['website']));
    _whatsapp = TextEditingController(text: _text(card['whatsapp_url']));
    _linkedin = TextEditingController(text: _text(card['linkedin_url']));
    _instagram = TextEditingController(text: _text(card['instagram_url']));
  }

  @override
  void dispose() {
    _jobTitle.dispose();
    _phone.dispose();
    _email.dispose();
    _website.dispose();
    _whatsapp.dispose();
    _linkedin.dispose();
    _instagram.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_companyId == null) {
      setState(() => _error = 'Selecciona una empresa.');
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });

    final payload = {
      'company': _companyId,
      'job_title': _jobTitle.text.trim(),
      'phone_number': _phone.text.trim(),
      'email': _email.text.trim(),
      'website': _url(_website.text),
      'whatsapp_url': _whatsappUrl(_whatsapp.text),
      'linkedin_url': _url(_linkedin.text),
      'instagram_url': _url(_instagram.text),
    };

    try {
      final repository = ref.read(cardRepositoryProvider);
      if (_isEditing) {
        final id = widget.card?['id'];
        if (id is! int) throw StateError('Tarjeta invalida.');
        await repository.updateDigital(id, payload);
      } else {
        await repository.createDigital(payload);
      }
      ref.invalidate(digitalCardsProvider);
      if (mounted) context.pop();
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'No pudimos guardar el perfil. Revisa los datos e intenta otra vez.');
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final companies = ref.watch(companiesProvider);

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
                        label: _isEditing ? 'Editar perfil' : 'Nuevo perfil',
                        icon: Icons.badge_rounded,
                        color: AppColors.gold,
                      ),
                      const SizedBox(height: 18),
                      Text(
                        _isEditing ? 'Actualizar perfil' : 'Crear perfil de negocio',
                        style: const TextStyle(fontSize: 30, height: 1.05, fontWeight: FontWeight.w900),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Este perfil sera la tarjeta digital publica del negocio.',
                        style: TextStyle(color: AppColors.muted, height: 1.45),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                GlassCard(
                  child: companies.when(
                    loading: () => const SizedBox(height: 120, child: AsyncStateView.loading()),
                    error: (_, __) => const AsyncStateView.error('No pudimos cargar tus empresas.'),
                    data: (items) => Column(
                      children: [
                        DropdownButtonFormField<int>(
                          value: _companyId,
                          items: [
                            for (final company in items)
                              DropdownMenuItem<int>(
                                value: _intValue(company['id']),
                                child: Text(_text(company['name'], fallback: 'Empresa')),
                              ),
                          ],
                          onChanged: _saving ? null : (value) => setState(() => _companyId = value),
                          validator: (value) => value == null ? 'Selecciona una empresa.' : null,
                          decoration: const InputDecoration(labelText: 'Empresa'),
                        ),
                        const SizedBox(height: 14),
                        _Field(controller: _jobTitle, label: 'Cargo', isRequired: true),
                        _Field(controller: _phone, label: 'Telefono', keyboardType: TextInputType.phone),
                        _Field(controller: _email, label: 'Email', keyboardType: TextInputType.emailAddress),
                        _Field(controller: _website, label: 'Website', keyboardType: TextInputType.url),
                        _Field(controller: _whatsapp, label: 'WhatsApp'),
                        _Field(controller: _linkedin, label: 'LinkedIn', keyboardType: TextInputType.url),
                        _Field(controller: _instagram, label: 'Instagram', keyboardType: TextInputType.url),
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
                          label: Text(_saving ? 'Guardando...' : 'Guardar perfil'),
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
    this.keyboardType,
  });

  final TextEditingController controller;
  final String label;
  final bool isRequired;
  final TextInputType? keyboardType;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: TextFormField(
        controller: controller,
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

String _text(dynamic value, {String fallback = ''}) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
}

int? _intValue(dynamic value) {
  if (value is int) return value;
  return int.tryParse(value?.toString() ?? '');
}

String _url(String value) {
  final text = value.trim();
  if (text.isEmpty) return '';
  return text.startsWith('http://') || text.startsWith('https://') ? text : 'https://$text';
}

String _whatsappUrl(String value) {
  final text = value.trim();
  if (text.isEmpty) return '';
  if (text.startsWith('http://') || text.startsWith('https://')) return text;
  final digits = text.replaceAll(RegExp(r'[^0-9+]'), '');
  return digits.isEmpty ? '' : 'https://wa.me/$digits';
}
