import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/companies/data/companies_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class CompanyFormScreen extends ConsumerStatefulWidget {
  const CompanyFormScreen({this.company, super.key});

  final Map<String, dynamic>? company;

  @override
  ConsumerState<CompanyFormScreen> createState() => _CompanyFormScreenState();
}

class _CompanyFormScreenState extends ConsumerState<CompanyFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _name;
  late final TextEditingController _description;
  late final TextEditingController _category;
  late final TextEditingController _services;
  late final TextEditingController _phone;
  late final TextEditingController _email;
  late final TextEditingController _website;
  late final TextEditingController _address;
  late final TextEditingController _city;
  late final TextEditingController _region;
  bool _saving = false;
  String? _error;

  bool get _isEditing => widget.company != null;

  @override
  void initState() {
    super.initState();
    final company = widget.company ?? const <String, dynamic>{};
    _name = TextEditingController(text: _text(company['name']));
    _description = TextEditingController(text: _text(company['description']));
    _category = TextEditingController(text: _text(company['category']));
    _services = TextEditingController(text: _text(company['services']));
    _phone = TextEditingController(text: _text(company['phone_number']));
    _email = TextEditingController(text: _text(company['email']));
    _website = TextEditingController(text: _text(company['website']));
    _address = TextEditingController(text: _text(company['address']));
    _city = TextEditingController(text: _text(company['city']));
    _region = TextEditingController(text: _text(company['region']));
  }

  @override
  void dispose() {
    _name.dispose();
    _description.dispose();
    _category.dispose();
    _services.dispose();
    _phone.dispose();
    _email.dispose();
    _website.dispose();
    _address.dispose();
    _city.dispose();
    _region.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _saving = true;
      _error = null;
    });

    final payload = {
      'name': _name.text.trim(),
      'description': _description.text.trim(),
      'category': _category.text.trim(),
      'services': _services.text.trim(),
      'phone_number': _phone.text.trim(),
      'email': _email.text.trim(),
      'website': _url(_website.text),
      'address': _address.text.trim(),
      'city': _city.text.trim(),
      'region': _region.text.trim(),
    };

    try {
      final repository = ref.read(companyRepositoryProvider);
      if (_isEditing) {
        final id = widget.company?['id'];
        if (id is! int) throw StateError('Empresa invalida.');
        await repository.update(id, payload);
      } else {
        await repository.create(payload);
      }
      ref.invalidate(companiesProvider);
      ref.invalidate(recommendedCompaniesProvider);
      if (mounted) context.pop();
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'No pudimos guardar la empresa. Revisa los datos e intenta otra vez.');
      }
    } finally {
      if (mounted) setState(() => _saving = false);
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
                        label: _isEditing ? 'Editar empresa' : 'Nueva empresa',
                        icon: Icons.business_center_rounded,
                        color: AppColors.gold,
                      ),
                      const SizedBox(height: 18),
                      Text(
                        _isEditing ? 'Actualizar empresa' : 'Crear empresa',
                        style: const TextStyle(fontSize: 30, height: 1.05, fontWeight: FontWeight.w900),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Completa la informacion publica y de contacto de tu negocio.',
                        style: TextStyle(color: AppColors.muted, height: 1.45),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                GlassCard(
                  child: Column(
                    children: [
                      _Field(controller: _name, label: 'Nombre', isRequired: true),
                      _Field(controller: _description, label: 'Descripcion', maxLines: 3),
                      _Field(controller: _category, label: 'Categoria'),
                      _Field(controller: _services, label: 'Servicios', maxLines: 3),
                      _Field(controller: _phone, label: 'Telefono', keyboardType: TextInputType.phone),
                      _Field(controller: _email, label: 'Email', keyboardType: TextInputType.emailAddress),
                      _Field(controller: _website, label: 'Website', keyboardType: TextInputType.url),
                      _Field(controller: _address, label: 'Direccion', maxLines: 2),
                      Row(
                        children: [
                          Expanded(child: _Field(controller: _city, label: 'Ciudad')),
                          const SizedBox(width: 10),
                          Expanded(child: _Field(controller: _region, label: 'Region')),
                        ],
                      ),
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
                        label: Text(_saving ? 'Guardando...' : 'Guardar empresa'),
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

String _url(String value) {
  final text = value.trim();
  if (text.isEmpty) return '';
  return text.startsWith('http://') || text.startsWith('https://') ? text : 'https://$text';
}
