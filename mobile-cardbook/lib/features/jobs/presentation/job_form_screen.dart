import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:mobile_cardbook/features/jobs/data/jobs_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class JobFormScreen extends ConsumerStatefulWidget {
  const JobFormScreen({this.job, super.key});

  final Map<String, dynamic>? job;

  @override
  ConsumerState<JobFormScreen> createState() => _JobFormScreenState();
}

class _JobFormScreenState extends ConsumerState<JobFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _picker = ImagePicker();
  late final TextEditingController _title;
  late final TextEditingController _phone;
  late final TextEditingController _address;
  late final TextEditingController _linkedin;
  late final TextEditingController _resume;
  late final TextEditingController _description;
  late final TextEditingController _experience;
  late final TextEditingController _languages;
  late final TextEditingController _technologies;
  late final TextEditingController _certifications;
  late final TextEditingController _availability;
  int? _specialtyId;
  bool _isAvailable = true;
  bool _saving = false;
  String _photoPath = '';
  String? _error;

  bool get _isEditing => widget.job != null;

  @override
  void initState() {
    super.initState();
    final job = widget.job ?? const <String, dynamic>{};
    _title = TextEditingController(
        text: _text(job['title'], fallback: 'Busco Trabajo'));
    _phone = TextEditingController(text: _text(job['phone_number']));
    _address = TextEditingController(text: _text(job['address']));
    _linkedin = TextEditingController(text: _text(job['linkedin_url']));
    _resume = TextEditingController(text: _text(job['resume_url']));
    _description = TextEditingController(text: _text(job['short_description']));
    _experience = TextEditingController(text: _text(job['experience']));
    _languages = TextEditingController(text: _text(job['languages']));
    _technologies = TextEditingController(text: _text(job['technologies']));
    _certifications = TextEditingController(text: _text(job['certifications']));
    _availability = TextEditingController(
        text: _text(job['availability_note'], fallback: 'Tiempo completo'));
    _specialtyId = _intValue(job['specialty']);
    _isAvailable = job['is_available'] != false;
  }

  @override
  void dispose() {
    _title.dispose();
    _phone.dispose();
    _address.dispose();
    _linkedin.dispose();
    _resume.dispose();
    _description.dispose();
    _experience.dispose();
    _languages.dispose();
    _technologies.dispose();
    _certifications.dispose();
    _availability.dispose();
    super.dispose();
  }

  Future<void> _pickPhoto(ImageSource source) async {
    final photo = await _picker.pickImage(
      source: source,
      maxWidth: 1400,
      imageQuality: 86,
    );
    if (photo == null) return;
    setState(() => _photoPath = photo.path);
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_specialtyId == null) {
      setState(() => _error = 'Selecciona una categoria de trabajo.');
      return;
    }

    setState(() {
      _saving = true;
      _error = null;
    });

    final payload = {
      'title': _title.text.trim(),
      'phone_number': _phone.text.trim(),
      'address': _address.text.trim(),
      'linkedin_url': _url(_linkedin.text),
      'resume_url': _url(_resume.text),
      'specialty': _specialtyId,
      'short_description': _description.text.trim(),
      'experience': _experience.text.trim(),
      'languages': _languages.text.trim(),
      'technologies': _technologies.text.trim(),
      'certifications': _certifications.text.trim(),
      'availability_note': _availability.text.trim(),
      'quote': '',
      'is_available': _isAvailable,
    };

    try {
      final repository = ref.read(jobRepositoryProvider);
      if (_isEditing) {
        await repository.update(payload, photoPath: _photoPath);
      } else {
        await repository.create(payload, photoPath: _photoPath);
      }
      ref.invalidate(mobileJobsProvider);
      if (mounted) context.pop();
    } catch (_) {
      if (mounted) {
        setState(() => _error =
            'No pudimos guardar tu White Card Job. Revisa los campos e intenta otra vez.');
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final specialties = ref.watch(jobSpecialtiesProvider);

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
                        label: _isEditing
                            ? 'Editar White Card'
                            : 'Nueva White Card',
                        icon: Icons.work_outline_rounded,
                        color: AppColors.gold,
                      ),
                      const SizedBox(height: 18),
                      Text(
                        _isEditing
                            ? 'Actualizar perfil laboral'
                            : 'Crear perfil laboral',
                        style: const TextStyle(
                          fontSize: 30,
                          height: 1.05,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Selecciona el tipo de trabajo y completa tu tarjeta blanca para empresas que buscan talento.',
                        style: TextStyle(color: AppColors.muted, height: 1.45),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                specialties.when(
                  loading: () => const SizedBox(
                    height: 160,
                    child: AsyncStateView.loading(),
                  ),
                  error: (_, __) => const AsyncStateView.error(
                    'No pudimos cargar las categorias de trabajo.',
                  ),
                  data: (items) => GlassCard(
                    child: Column(
                      children: [
                        DropdownButtonFormField<int>(
                          initialValue: _specialtyId,
                          items: [
                            for (final item in items)
                              DropdownMenuItem<int>(
                                value: _intValue(item['id']),
                                child: Text(_specialtyLabel(item)),
                              ),
                          ],
                          onChanged: _saving
                              ? null
                              : (value) => setState(() => _specialtyId = value),
                          validator: (value) => value == null
                              ? 'Selecciona una categoria.'
                              : null,
                          decoration: const InputDecoration(
                            labelText: 'Categoria de trabajo',
                            prefixIcon: Icon(Icons.category_rounded),
                          ),
                        ),
                        const SizedBox(height: 14),
                        _Field(
                            controller: _title,
                            label: 'Titulo',
                            isRequired: true),
                        _Field(
                          controller: _description,
                          label: 'Descripcion breve',
                          isRequired: true,
                          maxLines: 4,
                          maxLength: 420,
                        ),
                        _Field(
                            controller: _phone,
                            label: 'Telefono',
                            keyboardType: TextInputType.phone),
                        _Field(controller: _address, label: 'Ubicacion'),
                        _Field(
                            controller: _linkedin,
                            label: 'LinkedIn',
                            keyboardType: TextInputType.url),
                        _Field(
                            controller: _resume,
                            label: 'Resumen / CV URL',
                            keyboardType: TextInputType.url),
                        _Field(controller: _experience, label: 'Experiencia'),
                        _Field(controller: _languages, label: 'Idiomas'),
                        _Field(
                            controller: _technologies,
                            label: 'Habilidades / tecnologias',
                            maxLines: 2),
                        _Field(
                            controller: _certifications,
                            label: 'Certificaciones',
                            maxLines: 2),
                        _Field(
                            controller: _availability,
                            label: 'Disponibilidad',
                            isRequired: true),
                        SwitchListTile.adaptive(
                          value: _isAvailable,
                          onChanged: _saving
                              ? null
                              : (value) => setState(() => _isAvailable = value),
                          title: const Text('Disponible para ofertas'),
                          subtitle: const Text(
                              'Muestra tu tarjeta en busquedas publicas.'),
                        ),
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            Expanded(
                              child: OutlinedButton.icon(
                                onPressed: _saving
                                    ? null
                                    : () => _pickPhoto(ImageSource.gallery),
                                icon: const Icon(Icons.photo_library_rounded),
                                label: const Text('Galeria'),
                              ),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: OutlinedButton.icon(
                                onPressed: _saving
                                    ? null
                                    : () => _pickPhoto(ImageSource.camera),
                                icon: const Icon(Icons.photo_camera_rounded),
                                label: const Text('Camara'),
                              ),
                            ),
                          ],
                        ),
                        if (_photoPath.isNotEmpty) ...[
                          const SizedBox(height: 10),
                          const Text(
                            'Foto lista para subir.',
                            style: TextStyle(
                                color: AppColors.green,
                                fontWeight: FontWeight.w800),
                          ),
                        ],
                        if (_error != null) ...[
                          const SizedBox(height: 12),
                          Text(_error!,
                              style: const TextStyle(color: Colors.redAccent)),
                        ],
                        const SizedBox(height: 18),
                        FilledButton.icon(
                          onPressed: _saving ? null : _submit,
                          icon: _saving
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(
                                      strokeWidth: 2, color: Colors.white),
                                )
                              : const Icon(Icons.save_rounded),
                          label: Text(
                              _saving ? 'Guardando...' : 'Guardar White Card'),
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
    this.maxLength,
    this.keyboardType,
  });

  final TextEditingController controller;
  final String label;
  final bool isRequired;
  final int maxLines;
  final int? maxLength;
  final TextInputType? keyboardType;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: TextFormField(
        controller: controller,
        maxLines: maxLines,
        maxLength: maxLength,
        keyboardType: keyboardType,
        validator: isRequired
            ? (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Este campo es obligatorio.';
                }
                return null;
              }
            : null,
        decoration: InputDecoration(labelText: label),
      ),
    );
  }
}

String _specialtyLabel(Map<String, dynamic> item) {
  final category = _text(item['category']);
  final name = _text(item['name'], fallback: 'Trabajo');
  return category.isEmpty ? name : '$category - $name';
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
  return text.startsWith('http://') || text.startsWith('https://')
      ? text
      : 'https://$text';
}
