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
  int? _companyId;
  bool _saving = false;
  String? _error;

  bool get _isEditing => widget.card != null;

  @override
  void initState() {
    super.initState();
    final card = widget.card ?? const <String, dynamic>{};
    _profileId = _intValue(card['profile']);
    _companyId = _intValue(card['company']);
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
    if (_companyId == null) {
      setState(() => _error = 'Selecciona una empresa.');
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });

    try {
      final repository = ref.read(cardRepositoryProvider);
      final profileId = await _resolveProfileId(repository);
      final payload = {
        'profile': profileId,
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

  Future<int> _resolveProfileId(CardRepository repository) async {
    if (_profileId != null) return _profileId!;
    final profiles = ref.read(digitalCardsProvider).value ?? const <Map<String, dynamic>>[];
    for (final profile in profiles) {
      if (_intValue(profile['company']) == _companyId) {
        final id = _intValue(profile['id']);
        if (id != null) return id;
      }
    }

    final profile = await repository.createDigital({
      'company': _companyId,
      'job_title': _jobTitle.text.trim(),
      'phone_number': _phone.text.trim(),
      'email': _email.text.trim(),
      'website': _url(_website.text),
    });
    ref.invalidate(digitalCardsProvider);
    final id = _intValue(profile['id']);
    if (id == null) throw StateError('No se pudo crear el perfil base.');
    _profileId = id;
    return id;
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
                  child: companies.when(
                    loading: () => const SizedBox(height: 120, child: AsyncStateView.loading()),
                    error: (_, __) => const AsyncStateView.error('No pudimos cargar tus empresas.'),
                    data: (items) => Column(
                      children: [
                        if (items.isEmpty) ...[
                          const AsyncStateView.empty('Primero crea una empresa para asociar esta tarjeta.'),
                          const SizedBox(height: 12),
                          OutlinedButton.icon(
                            onPressed: _saving ? null : () => context.push('/companies/form'),
                            icon: const Icon(Icons.add_business_rounded),
                            label: const Text('Crear empresa'),
                          ),
                          const SizedBox(height: 14),
                        ],
                        DropdownButtonFormField<int>(
                          value: _companyId,
                          items: [
                            for (final company in items)
                              DropdownMenuItem<int>(
                                value: _intValue(company['id']),
                                child: Text(_text(company['name'])),
                              ),
                          ],
                          onChanged: _saving
                              ? null
                              : (value) {
                                  Map<String, dynamic>? selected;
                                  for (final item in items) {
                                    if (_intValue(item['id']) == value) {
                                      selected = item;
                                      break;
                                    }
                                  }
                                  setState(() {
                                    _companyId = value;
                                    _profileId = null;
                                    if (_companyName.text.trim().isEmpty && selected != null) {
                                      _companyName.text = _text(selected['name']);
                                    }
                                  });
                                },
                          validator: (value) => value == null ? 'Selecciona una empresa.' : null,
                          decoration: const InputDecoration(labelText: 'Empresa'),
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
