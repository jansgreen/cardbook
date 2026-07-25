import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:mobile_cardbook/features/cards/data/physical_card_ocr.dart';
import 'package:mobile_cardbook/features/jobs/data/job_card_draft_store.dart';
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
  bool _assimilating = false;
  bool _draftBusy = false;
  bool _hasDraft = false;
  String _photoPath = '';
  XFile? _frontScan;
  XFile? _backScan;
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
    if (!_isEditing) {
      Future.microtask(_loadDraftState);
    }
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
    if (!_isEditing) {
      await _saveDraft(silent: true);
    }
  }

  Future<void> _pickPhysicalCardScan({
    required bool front,
    required ImageSource source,
  }) async {
    final image = await _picker.pickImage(
      source: source,
      maxWidth: 1800,
      imageQuality: 88,
    );
    if (image == null) return;
    setState(() {
      if (front) {
        _frontScan = image;
      } else {
        _backScan = image;
      }
    });
    if (!_isEditing) {
      await _saveDraft(silent: true);
    }
  }

  Future<void> _assimilateFrontScan() async {
    final scan = _frontScan;
    if (scan == null || _assimilating) return;
    setState(() {
      _assimilating = true;
      _error = null;
    });
    try {
      final result = await PhysicalCardOcr.extract(scan.path);
      _applyOcrResult(result);
      if (!_isEditing) {
        await _saveDraft(silent: true);
      }
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result.filledCount > 0
              ? 'Datos detectados: ${result.filledCount}. Revisa antes de guardar.'
              : 'No detectamos datos claros. Puedes completarlos manualmente.'),
        ),
      );
    } catch (_) {
      if (mounted) {
        setState(() => _error =
            'No pudimos leer la tarjeta laboral. Intenta con mejor luz y enfoque.');
      }
    } finally {
      if (mounted) setState(() => _assimilating = false);
    }
  }

  void _applyOcrResult(PhysicalCardOcrResult result) {
    void fill(TextEditingController controller, String value) {
      if (controller.text.trim().isEmpty && value.trim().isNotEmpty) {
        controller.text = value.trim();
      }
    }

    void fillWhenDefault(
      TextEditingController controller,
      String value,
      String defaultValue,
    ) {
      final current = controller.text.trim().toLowerCase();
      if ((current.isEmpty || current == defaultValue.toLowerCase()) &&
          value.trim().isNotEmpty) {
        controller.text = value.trim();
      }
    }

    fillWhenDefault(_title, result.jobTitle, 'Busco Trabajo');
    fill(_phone, result.phone);
    fill(_address, result.address);
    final website = result.website;
    if (website.toLowerCase().contains('linkedin')) {
      fill(_linkedin, website);
    } else {
      fill(_resume, website);
    }
    fill(_description, result.services);
    fill(_technologies, result.services);
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
      if (_frontScan != null || _backScan != null)
        'is_physical_card_imported': true,
      if (_frontScan != null) '_physical_card_front_path': _frontScan!.path,
      if (_backScan != null) '_physical_card_back_path': _backScan!.path,
    };

    try {
      final repository = ref.read(jobRepositoryProvider);
      if (_isEditing) {
        await repository.update(payload, photoPath: _photoPath);
      } else {
        await repository.create(payload, photoPath: _photoPath);
        await ref.read(jobCardDraftStoreProvider).clear();
        ref.invalidate(jobCardDraftProvider);
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

  Future<void> _loadDraftState() async {
    final draft = await ref.read(jobCardDraftStoreProvider).read();
    if (!mounted) return;
    setState(() => _hasDraft = draft != null);
  }

  JobCardDraft _currentDraft() {
    return JobCardDraft(
      specialtyId: _specialtyId,
      title: _title.text.trim(),
      phone: _phone.text.trim(),
      address: _address.text.trim(),
      linkedin: _linkedin.text.trim(),
      resume: _resume.text.trim(),
      description: _description.text.trim(),
      experience: _experience.text.trim(),
      languages: _languages.text.trim(),
      technologies: _technologies.text.trim(),
      certifications: _certifications.text.trim(),
      availability: _availability.text.trim(),
      isAvailable: _isAvailable,
      photoPath: _photoPath,
      frontScanPath: _frontScan?.path ?? '',
      backScanPath: _backScan?.path ?? '',
      updatedAt: DateTime.now(),
    );
  }

  Future<void> _saveDraft({bool silent = false}) async {
    if (_isEditing || _draftBusy) return;
    setState(() {
      _draftBusy = true;
      _error = null;
    });
    try {
      final draft = _currentDraft();
      if (!draft.hasContent) return;
      await ref.read(jobCardDraftStoreProvider).save(draft);
      ref.invalidate(jobCardDraftProvider);
      if (!mounted) return;
      setState(() => _hasDraft = true);
      if (!silent) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Borrador laboral guardado.')),
        );
      }
    } catch (_) {
      if (mounted && !silent) {
        setState(() => _error = 'No pudimos guardar el borrador laboral.');
      }
    } finally {
      if (mounted) setState(() => _draftBusy = false);
    }
  }

  Future<void> _restoreDraft() async {
    if (_isEditing || _draftBusy) return;
    setState(() {
      _draftBusy = true;
      _error = null;
    });
    try {
      final draft = await ref.read(jobCardDraftStoreProvider).read();
      if (draft == null) {
        if (mounted) setState(() => _hasDraft = false);
        return;
      }
      await _applyDraft(draft);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'No pudimos restaurar el borrador laboral.');
      }
    } finally {
      if (mounted) setState(() => _draftBusy = false);
    }
  }

  Future<void> _syncDraft() async {
    if (_isEditing || _saving || _draftBusy) return;
    final draft = await ref.read(jobCardDraftStoreProvider).read();
    if (draft == null) {
      if (mounted) setState(() => _hasDraft = false);
      return;
    }
    if (draft.specialtyId == null ||
        draft.title.trim().isEmpty ||
        draft.description.trim().isEmpty) {
      await _applyDraft(draft, showMessage: false);
      if (!mounted) return;
      setState(() => _error =
          'Completa categoria, titulo y descripcion antes de publicar el borrador.');
      return;
    }

    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await _applyDraft(draft, showMessage: false);
      final repository = ref.read(jobRepositoryProvider);
      final payload = _payloadFromDraft(draft);
      await repository.create(payload, photoPath: _photoPath);
      await ref.read(jobCardDraftStoreProvider).clear();
      ref.invalidate(jobCardDraftProvider);
      ref.invalidate(mobileJobsProvider);
      if (!mounted) return;
      setState(() => _hasDraft = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Borrador laboral publicado.')),
      );
      context.pop();
    } catch (_) {
      if (mounted) {
        setState(() => _error =
            'No pudimos publicar el borrador laboral. Revisa tu conexion.');
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _clearDraft() async {
    if (_isEditing || _draftBusy) return;
    setState(() {
      _draftBusy = true;
      _error = null;
    });
    try {
      await ref.read(jobCardDraftStoreProvider).clear();
      ref.invalidate(jobCardDraftProvider);
      if (!mounted) return;
      setState(() => _hasDraft = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Borrador laboral descartado.')),
      );
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'No pudimos descartar el borrador laboral.');
      }
    } finally {
      if (mounted) setState(() => _draftBusy = false);
    }
  }

  Future<void> _applyDraft(JobCardDraft draft,
      {bool showMessage = true}) async {
    final photoExists = await _pathExists(draft.photoPath);
    final frontScan = await _scanFromPath(draft.frontScanPath);
    final backScan = await _scanFromPath(draft.backScanPath);
    if (!mounted) return;
    setState(() {
      _specialtyId = draft.specialtyId;
      _title.text = draft.title;
      _phone.text = draft.phone;
      _address.text = draft.address;
      _linkedin.text = draft.linkedin;
      _resume.text = draft.resume;
      _description.text = draft.description;
      _experience.text = draft.experience;
      _languages.text = draft.languages;
      _technologies.text = draft.technologies;
      _certifications.text = draft.certifications;
      _availability.text = draft.availability;
      _isAvailable = draft.isAvailable;
      _photoPath = photoExists ? draft.photoPath : '';
      _frontScan = frontScan;
      _backScan = backScan;
      _hasDraft = true;
    });
    if (showMessage) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Borrador laboral restaurado.')),
      );
    }
  }

  Map<String, dynamic> _payloadFromDraft(JobCardDraft draft) {
    final frontPath = _frontScan?.path ?? '';
    final backPath = _backScan?.path ?? '';
    return {
      'title': draft.title.trim(),
      'phone_number': draft.phone.trim(),
      'address': draft.address.trim(),
      'linkedin_url': _url(draft.linkedin),
      'resume_url': _url(draft.resume),
      'specialty': draft.specialtyId,
      'short_description': draft.description.trim(),
      'experience': draft.experience.trim(),
      'languages': draft.languages.trim(),
      'technologies': draft.technologies.trim(),
      'certifications': draft.certifications.trim(),
      'availability_note': draft.availability.trim(),
      'quote': '',
      'is_available': draft.isAvailable,
      if (frontPath.isNotEmpty || backPath.isNotEmpty)
        'is_physical_card_imported': true,
      if (frontPath.isNotEmpty) '_physical_card_front_path': frontPath,
      if (backPath.isNotEmpty) '_physical_card_back_path': backPath,
    };
  }

  Future<XFile?> _scanFromPath(String path) async {
    if (!await _pathExists(path)) return null;
    return XFile(path);
  }

  Future<bool> _pathExists(String path) async {
    if (path.trim().isEmpty) return false;
    return File(path).exists();
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
                        const SizedBox(height: 14),
                        _PhysicalJobCardScanner(
                          frontScan: _frontScan,
                          backScan: _backScan,
                          existingFrontUrl:
                              _text(widget.job?['physical_card_front_image']),
                          existingBackUrl:
                              _text(widget.job?['physical_card_back_image']),
                          onPickFrontCamera: _saving
                              ? null
                              : () => _pickPhysicalCardScan(
                                  front: true, source: ImageSource.camera),
                          onPickFrontGallery: _saving
                              ? null
                              : () => _pickPhysicalCardScan(
                                  front: true, source: ImageSource.gallery),
                          onPickBackCamera: _saving
                              ? null
                              : () => _pickPhysicalCardScan(
                                  front: false, source: ImageSource.camera),
                          onPickBackGallery: _saving
                              ? null
                              : () => _pickPhysicalCardScan(
                                  front: false, source: ImageSource.gallery),
                          onClearFront: _saving
                              ? null
                              : () => setState(() => _frontScan = null),
                          onClearBack: _saving
                              ? null
                              : () => setState(() => _backScan = null),
                          onAssimilate: _saving || _frontScan == null
                              ? null
                              : _assimilateFrontScan,
                          assimilating: _assimilating,
                          hasDraft: _hasDraft,
                          draftBusy: _draftBusy,
                          onSaveDraft:
                              _saving || _isEditing ? null : () => _saveDraft(),
                          onRestoreDraft: _saving || _isEditing || !_hasDraft
                              ? null
                              : _restoreDraft,
                          onSyncDraft: _saving || _isEditing || !_hasDraft
                              ? null
                              : _syncDraft,
                          onClearDraft: _saving || _isEditing || !_hasDraft
                              ? null
                              : _clearDraft,
                        ),
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

class _PhysicalJobCardScanner extends StatelessWidget {
  const _PhysicalJobCardScanner({
    required this.frontScan,
    required this.backScan,
    required this.existingFrontUrl,
    required this.existingBackUrl,
    required this.onPickFrontCamera,
    required this.onPickFrontGallery,
    required this.onPickBackCamera,
    required this.onPickBackGallery,
    required this.onClearFront,
    required this.onClearBack,
    required this.onAssimilate,
    required this.assimilating,
    required this.hasDraft,
    required this.draftBusy,
    required this.onSaveDraft,
    required this.onRestoreDraft,
    required this.onSyncDraft,
    required this.onClearDraft,
  });

  final XFile? frontScan;
  final XFile? backScan;
  final String existingFrontUrl;
  final String existingBackUrl;
  final VoidCallback? onPickFrontCamera;
  final VoidCallback? onPickFrontGallery;
  final VoidCallback? onPickBackCamera;
  final VoidCallback? onPickBackGallery;
  final VoidCallback? onClearFront;
  final VoidCallback? onClearBack;
  final VoidCallback? onAssimilate;
  final bool assimilating;
  final bool hasDraft;
  final bool draftBusy;
  final VoidCallback? onSaveDraft;
  final VoidCallback? onRestoreDraft;
  final VoidCallback? onSyncDraft;
  final VoidCallback? onClearDraft;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.inkAlt.withValues(alpha: .55),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.stroke),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.document_scanner_rounded,
                  color: AppColors.gold, size: 20),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Importar tarjeta laboral fisica',
                  style: TextStyle(fontWeight: FontWeight.w900),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          const Text(
            'Si ya tienes una tarjeta laboral impresa, captura el frente y el reverso. Cardbook la guardara como parte de tu White Card y mantendra tu QR publico.',
            style:
                TextStyle(color: AppColors.muted, fontSize: 12, height: 1.35),
          ),
          const SizedBox(height: 14),
          FilledButton.icon(
            onPressed: onAssimilate,
            icon: assimilating
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.auto_fix_high_rounded),
            label: Text(assimilating
                ? 'Leyendo tarjeta...'
                : 'Asimilar datos del frente'),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              OutlinedButton.icon(
                onPressed: draftBusy ? null : onSaveDraft,
                icon: draftBusy
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.save_as_rounded),
                label: const Text('Guardar borrador'),
              ),
              OutlinedButton.icon(
                onPressed: draftBusy || !hasDraft ? null : onRestoreDraft,
                icon: const Icon(Icons.restore_rounded),
                label: const Text('Restaurar'),
              ),
              FilledButton.icon(
                onPressed: draftBusy || !hasDraft ? null : onSyncDraft,
                icon: const Icon(Icons.cloud_upload_rounded),
                label: const Text('Publicar'),
              ),
              TextButton.icon(
                onPressed: draftBusy || !hasDraft ? null : onClearDraft,
                icon: const Icon(Icons.delete_outline_rounded),
                label: const Text('Descartar'),
              ),
            ],
          ),
          const SizedBox(height: 14),
          _JobScanSlot(
            title: 'Frente',
            scan: frontScan,
            existingUrl: existingFrontUrl,
            onCamera: onPickFrontCamera,
            onGallery: onPickFrontGallery,
            onClear: onClearFront,
          ),
          const SizedBox(height: 12),
          _JobScanSlot(
            title: 'Reverso',
            scan: backScan,
            existingUrl: existingBackUrl,
            onCamera: onPickBackCamera,
            onGallery: onPickBackGallery,
            onClear: onClearBack,
          ),
        ],
      ),
    );
  }
}

class _JobScanSlot extends StatelessWidget {
  const _JobScanSlot({
    required this.title,
    required this.scan,
    required this.existingUrl,
    required this.onCamera,
    required this.onGallery,
    required this.onClear,
  });

  final String title;
  final XFile? scan;
  final String existingUrl;
  final VoidCallback? onCamera;
  final VoidCallback? onGallery;
  final VoidCallback? onClear;

  @override
  Widget build(BuildContext context) {
    final hasImage = scan != null || existingUrl.isNotEmpty;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              title,
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w900),
            ),
            const Spacer(),
            if (scan != null)
              TextButton.icon(
                onPressed: onClear,
                icon: const Icon(Icons.close_rounded, size: 16),
                label: const Text('Quitar'),
              ),
          ],
        ),
        const SizedBox(height: 8),
        AspectRatio(
          aspectRatio: 1.75,
          child: Container(
            clipBehavior: Clip.antiAlias,
            decoration: BoxDecoration(
              color: AppColors.panelSoft.withValues(alpha: .7),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.stroke),
            ),
            child: hasImage
                ? _JobScanImage(scan: scan, existingUrl: existingUrl)
                : const Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.work_outline_rounded,
                            color: AppColors.muted, size: 34),
                        SizedBox(height: 8),
                        Text(
                          'Sin captura',
                          style:
                              TextStyle(color: AppColors.muted, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: onCamera,
                icon: const Icon(Icons.photo_camera_rounded),
                label: const Text('Camara'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: onGallery,
                icon: const Icon(Icons.photo_library_rounded),
                label: const Text('Galeria'),
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _JobScanImage extends StatelessWidget {
  const _JobScanImage({required this.scan, required this.existingUrl});

  final XFile? scan;
  final String existingUrl;

  @override
  Widget build(BuildContext context) {
    if (scan != null) {
      return Image.file(File(scan!.path), fit: BoxFit.cover);
    }
    return Image.network(existingUrl, fit: BoxFit.cover);
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
