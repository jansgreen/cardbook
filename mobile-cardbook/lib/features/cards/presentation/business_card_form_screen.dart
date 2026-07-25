import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:mobile_cardbook/features/cards/data/business_card_draft_store.dart';
import 'package:mobile_cardbook/features/cards/data/cards_repository.dart';
import 'package:mobile_cardbook/features/cards/data/physical_card_ocr.dart';
import 'package:mobile_cardbook/features/companies/data/companies_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class BusinessCardFormScreen extends ConsumerStatefulWidget {
  const BusinessCardFormScreen({this.card, this.initialCompany, super.key});

  final Map<String, dynamic>? card;
  final Map<String, dynamic>? initialCompany;

  @override
  ConsumerState<BusinessCardFormScreen> createState() =>
      _BusinessCardFormScreenState();
}

class _BusinessCardFormScreenState
    extends ConsumerState<BusinessCardFormScreen> {
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
  final _imagePicker = ImagePicker();
  XFile? _frontScan;
  XFile? _backScan;
  bool _saving = false;
  bool _assimilating = false;
  bool _draftBusy = false;
  bool _hasDraft = false;
  String? _error;

  bool get _isEditing => widget.card != null;

  @override
  void initState() {
    super.initState();
    final card = widget.card ?? const <String, dynamic>{};
    final initialCompany = widget.initialCompany ?? const <String, dynamic>{};
    _profileId = _intValue(card['profile']);
    _companyId = _intValue(card['company']) ?? _intValue(initialCompany['id']);
    _displayName = TextEditingController(text: _text(card['display_name']));
    _jobTitle = TextEditingController(text: _text(card['job_title']));
    _companyName = TextEditingController(
        text: _firstText([card['company_name'], initialCompany['name']]));
    _phone = TextEditingController(
        text:
            _firstText([card['phone_number'], initialCompany['phone_number']]));
    _email = TextEditingController(
        text: _firstText([card['email'], initialCompany['email']]));
    _website = TextEditingController(
        text: _firstText([card['website'], initialCompany['website']]));
    _address = TextEditingController(
        text: _firstText([card['address'], initialCompany['address']]));
    _tagline = TextEditingController(text: _text(card['tagline']));
    _services = TextEditingController(text: _text(card['services']));
    if (!_isEditing) {
      Future.microtask(_loadDraftState);
    }
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
        if (_frontScan != null || _backScan != null)
          'is_physical_card_imported': true,
        if (_frontScan != null) '_physical_card_front_path': _frontScan!.path,
        if (_backScan != null) '_physical_card_back_path': _backScan!.path,
      };

      if (_isEditing) {
        final id = widget.card?['id'];
        if (id is! int) throw StateError('Tarjeta invalida.');
        await repository.updateBusiness(id, payload);
      } else {
        await repository.createBusiness(payload);
        await ref.read(businessCardDraftStoreProvider).clear();
        ref.invalidate(businessCardDraftProvider);
      }
      ref.invalidate(businessCardsProvider);
      if (mounted) context.pop();
    } catch (_) {
      if (mounted) {
        setState(() => _error =
            'No pudimos guardar la tarjeta. Revisa los datos e intenta otra vez.');
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _syncDraft() async {
    if (_isEditing || _saving || _draftBusy) return;
    final draft = await ref.read(businessCardDraftStoreProvider).read();
    if (draft == null) {
      if (mounted) setState(() => _hasDraft = false);
      return;
    }
    if (draft.companyId == null ||
        draft.displayName.trim().isEmpty ||
        draft.companyName.trim().isEmpty) {
      await _restoreDraft();
      if (!mounted) return;
      setState(() => _error =
          'Completa empresa, nombre visible y empresa antes de publicar el borrador.');
      return;
    }

    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final repository = ref.read(cardRepositoryProvider);
      await _applyDraft(draft, silent: true);
      final profileId = await _resolveProfileId(repository);
      final frontScanPath = _frontScan?.path ?? '';
      final backScanPath = _backScan?.path ?? '';
      final payload = {
        'profile': profileId,
        'display_name': draft.displayName.trim(),
        'job_title': draft.jobTitle.trim(),
        'company_name': draft.companyName.trim(),
        'phone_number': draft.phone.trim(),
        'email': draft.email.trim(),
        'website': _url(draft.website),
        'address': draft.address.trim(),
        'tagline': draft.tagline.trim(),
        'services': draft.services.trim(),
        if (frontScanPath.isNotEmpty || backScanPath.isNotEmpty)
          'is_physical_card_imported': true,
        if (frontScanPath.isNotEmpty)
          '_physical_card_front_path': frontScanPath,
        if (backScanPath.isNotEmpty) '_physical_card_back_path': backScanPath,
      };
      await repository.createBusiness(payload);
      await ref.read(businessCardDraftStoreProvider).clear();
      ref.invalidate(businessCardsProvider);
      ref.invalidate(businessCardDraftProvider);
      if (!mounted) return;
      setState(() => _hasDraft = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Borrador publicado correctamente.')),
      );
      context.pop();
    } catch (_) {
      if (mounted) {
        setState(() => _error =
            'No pudimos publicar el borrador. Revisa tu conexion e intenta otra vez.');
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<int> _resolveProfileId(CardRepository repository) async {
    if (_profileId != null) return _profileId!;
    final profiles =
        ref.read(digitalCardsProvider).value ?? const <Map<String, dynamic>>[];
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

  Future<void> _pickScan({
    required bool front,
    required ImageSource source,
  }) async {
    final image = await _imagePicker.pickImage(
      source: source,
      imageQuality: 88,
      maxWidth: 1800,
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
            'No pudimos leer la imagen. Intenta con mejor luz y enfoque.');
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

    fill(_displayName, result.displayName);
    fill(_jobTitle, result.jobTitle);
    fill(_companyName, result.companyName);
    fill(_phone, result.phone);
    fill(_email, result.email);
    fill(_website, result.website);
    fill(_address, result.address);
    fill(_services, result.services);
  }

  Future<void> _loadDraftState() async {
    final draft = await ref.read(businessCardDraftStoreProvider).read();
    if (!mounted) return;
    setState(() => _hasDraft = draft != null);
  }

  Future<void> _saveDraft({bool silent = false}) async {
    if (_isEditing || _draftBusy) return;
    setState(() {
      _draftBusy = true;
      _error = null;
    });
    try {
      final draft = BusinessCardDraft(
        profileId: _profileId,
        companyId: _companyId,
        displayName: _displayName.text.trim(),
        jobTitle: _jobTitle.text.trim(),
        companyName: _companyName.text.trim(),
        phone: _phone.text.trim(),
        email: _email.text.trim(),
        website: _website.text.trim(),
        address: _address.text.trim(),
        tagline: _tagline.text.trim(),
        services: _services.text.trim(),
        frontScanPath: _frontScan?.path ?? '',
        backScanPath: _backScan?.path ?? '',
        updatedAt: DateTime.now(),
      );
      if (!draft.hasContent) return;
      await ref.read(businessCardDraftStoreProvider).save(draft);
      ref.invalidate(businessCardDraftProvider);
      if (!mounted) return;
      setState(() => _hasDraft = true);
      if (!silent) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text('Borrador guardado en este dispositivo.')),
        );
      }
    } catch (_) {
      if (mounted && !silent) {
        setState(() => _error = 'No pudimos guardar el borrador local.');
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
      final draft = await ref.read(businessCardDraftStoreProvider).read();
      if (draft == null) {
        if (mounted) setState(() => _hasDraft = false);
        return;
      }
      final frontScan = await _scanFromPath(draft.frontScanPath);
      final backScan = await _scanFromPath(draft.backScanPath);
      if (!mounted) return;
      _applyDraftValues(draft, frontScan: frontScan, backScan: backScan);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Borrador restaurado.')),
      );
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'No pudimos restaurar el borrador.');
      }
    } finally {
      if (mounted) setState(() => _draftBusy = false);
    }
  }

  Future<void> _applyDraft(BusinessCardDraft draft,
      {bool silent = false}) async {
    final frontScan = await _scanFromPath(draft.frontScanPath);
    final backScan = await _scanFromPath(draft.backScanPath);
    if (!mounted) return;
    _applyDraftValues(draft, frontScan: frontScan, backScan: backScan);
    if (!silent) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Borrador restaurado.')),
      );
    }
  }

  void _applyDraftValues(
    BusinessCardDraft draft, {
    required XFile? frontScan,
    required XFile? backScan,
  }) {
    setState(() {
      _profileId = draft.profileId;
      _companyId = draft.companyId;
      _displayName.text = draft.displayName;
      _jobTitle.text = draft.jobTitle;
      _companyName.text = draft.companyName;
      _phone.text = draft.phone;
      _email.text = draft.email;
      _website.text = draft.website;
      _address.text = draft.address;
      _tagline.text = draft.tagline;
      _services.text = draft.services;
      _frontScan = frontScan;
      _backScan = backScan;
      _hasDraft = true;
    });
  }

  Future<void> _clearDraft() async {
    if (_isEditing || _draftBusy) return;
    setState(() {
      _draftBusy = true;
      _error = null;
    });
    try {
      await ref.read(businessCardDraftStoreProvider).clear();
      ref.invalidate(businessCardDraftProvider);
      if (!mounted) return;
      setState(() => _hasDraft = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Borrador descartado.')),
      );
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'No pudimos descartar el borrador.');
      }
    } finally {
      if (mounted) setState(() => _draftBusy = false);
    }
  }

  Future<XFile?> _scanFromPath(String path) async {
    if (path.trim().isEmpty) return null;
    final file = File(path);
    if (!await file.exists()) return null;
    return XFile(path);
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
                        label: _isEditing
                            ? 'Editar presentacion'
                            : 'Nueva presentacion',
                        icon: Icons.contact_page_rounded,
                        color: AppColors.gold,
                      ),
                      const SizedBox(height: 18),
                      Text(
                        _isEditing
                            ? 'Actualizar tarjeta'
                            : 'Crear tarjeta de presentacion',
                        style: const TextStyle(
                            fontSize: 30,
                            height: 1.05,
                            fontWeight: FontWeight.w900),
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
                    loading: () => const SizedBox(
                        height: 120, child: AsyncStateView.loading()),
                    error: (_, __) => const AsyncStateView.error(
                        'No pudimos cargar tus empresas.'),
                    data: (items) => Column(
                      children: [
                        if (items.isEmpty) ...[
                          const AsyncStateView.empty(
                              'Primero crea una empresa para asociar esta tarjeta.'),
                          const SizedBox(height: 12),
                          OutlinedButton.icon(
                            onPressed: _saving
                                ? null
                                : () => context.push('/companies/form'),
                            icon: const Icon(Icons.add_business_rounded),
                            label: const Text('Crear empresa'),
                          ),
                          const SizedBox(height: 14),
                        ],
                        DropdownButtonFormField<int>(
                          initialValue: _companyId,
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
                                    if (_companyName.text.trim().isEmpty &&
                                        selected != null) {
                                      _companyName.text =
                                          _text(selected['name']);
                                    }
                                  });
                                },
                          validator: (value) =>
                              value == null ? 'Selecciona una empresa.' : null,
                          decoration:
                              const InputDecoration(labelText: 'Empresa'),
                        ),
                        const SizedBox(height: 14),
                        _Field(
                            controller: _displayName,
                            label: 'Nombre visible',
                            isRequired: true),
                        _Field(controller: _jobTitle, label: 'Cargo'),
                        _Field(
                            controller: _companyName,
                            label: 'Empresa',
                            isRequired: true),
                        _Field(
                            controller: _phone,
                            label: 'Telefono',
                            keyboardType: TextInputType.phone),
                        _Field(
                            controller: _email,
                            label: 'Email',
                            keyboardType: TextInputType.emailAddress),
                        _Field(
                            controller: _website,
                            label: 'Website',
                            keyboardType: TextInputType.url),
                        _Field(
                            controller: _address,
                            label: 'Direccion',
                            maxLines: 2),
                        _Field(controller: _tagline, label: 'Frase corta'),
                        _Field(
                            controller: _services,
                            label: 'Servicios',
                            maxLines: 3),
                        const SizedBox(height: 4),
                        _PhysicalCardScanner(
                          frontScan: _frontScan,
                          backScan: _backScan,
                          existingFrontUrl:
                              _text(widget.card?['physical_card_front_image']),
                          existingBackUrl:
                              _text(widget.card?['physical_card_back_image']),
                          onPickFrontCamera: _saving
                              ? null
                              : () => _pickScan(
                                  front: true, source: ImageSource.camera),
                          onPickFrontGallery: _saving
                              ? null
                              : () => _pickScan(
                                  front: true, source: ImageSource.gallery),
                          onPickBackCamera: _saving
                              ? null
                              : () => _pickScan(
                                  front: false, source: ImageSource.camera),
                          onPickBackGallery: _saving
                              ? null
                              : () => _pickScan(
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
                          onClearDraft: _saving || _isEditing || !_hasDraft
                              ? null
                              : _clearDraft,
                          onSyncDraft: _saving || _isEditing || !_hasDraft
                              ? null
                              : _syncDraft,
                        ),
                        if (_error != null) ...[
                          const SizedBox(height: 8),
                          Text(_error!,
                              style: const TextStyle(color: Colors.redAccent)),
                        ],
                        const SizedBox(height: 16),
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
                              _saving ? 'Guardando...' : 'Guardar tarjeta'),
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

class _PhysicalCardScanner extends StatelessWidget {
  const _PhysicalCardScanner({
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
    required this.onClearDraft,
    required this.onSyncDraft,
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
  final VoidCallback? onClearDraft;
  final VoidCallback? onSyncDraft;

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
                  'Escanear tarjeta fisica',
                  style: TextStyle(fontWeight: FontWeight.w900),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          const Text(
            'Captura una tarjeta que ya tengas. Cardbook la guardara como referencia visual y seguira generando QR, enlace publico y acciones nativas.',
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
                label: const Text('Publicar borrador'),
              ),
              TextButton.icon(
                onPressed: draftBusy || !hasDraft ? null : onClearDraft,
                icon: const Icon(Icons.delete_outline_rounded),
                label: const Text('Descartar'),
              ),
            ],
          ),
          const SizedBox(height: 14),
          _ScanSlot(
            title: 'Frente',
            scan: frontScan,
            existingUrl: existingFrontUrl,
            onCamera: onPickFrontCamera,
            onGallery: onPickFrontGallery,
            onClear: onClearFront,
          ),
          const SizedBox(height: 12),
          _ScanSlot(
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

class _ScanSlot extends StatelessWidget {
  const _ScanSlot({
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
            Text(title,
                style:
                    const TextStyle(fontSize: 13, fontWeight: FontWeight.w900)),
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
                ? _ScanImage(scan: scan, existingUrl: existingUrl)
                : const Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.credit_card_rounded,
                            color: AppColors.muted, size: 34),
                        SizedBox(height: 8),
                        Text('Sin captura',
                            style: TextStyle(
                                color: AppColors.muted, fontSize: 12)),
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

class _ScanImage extends StatelessWidget {
  const _ScanImage({required this.scan, required this.existingUrl});

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

String _text(dynamic value) => value?.toString().trim() ?? '';

int? _intValue(dynamic value) {
  if (value is int) return value;
  if (value is Map<String, dynamic>) return _intValue(value['id']);
  return int.tryParse(value?.toString() ?? '');
}

String _firstText(List<dynamic> values) {
  for (final value in values) {
    final text = _text(value);
    if (text.isNotEmpty) return text;
  }
  return '';
}

String _url(String value) {
  final text = value.trim();
  if (text.isEmpty) return '';
  return text.startsWith('http://') || text.startsWith('https://')
      ? text
      : 'https://$text';
}
