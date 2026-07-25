import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_cardbook/core/platform/native_actions.dart';
import 'package:mobile_cardbook/features/ai_agents/data/ai_agents_repository.dart';
import 'package:mobile_cardbook/features/home/data/mobile_bootstrap_repository.dart';
import 'package:mobile_cardbook/shared/theme/app_theme.dart';
import 'package:mobile_cardbook/shared/widgets/app_bottom_nav.dart';
import 'package:mobile_cardbook/shared/widgets/app_gradient_background.dart';
import 'package:mobile_cardbook/shared/widgets/async_state_view.dart';
import 'package:mobile_cardbook/shared/widgets/brand_header.dart';
import 'package:mobile_cardbook/shared/widgets/glass_card.dart';
import 'package:mobile_cardbook/shared/widgets/section_header.dart';
import 'package:mobile_cardbook/shared/widgets/status_badge.dart';

class AIAgentsScreen extends ConsumerStatefulWidget {
  const AIAgentsScreen({super.key});

  @override
  ConsumerState<AIAgentsScreen> createState() => _AIAgentsScreenState();
}

class _AIAgentsScreenState extends ConsumerState<AIAgentsScreen> {
  final _search = TextEditingController();

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final payload = ref.watch(mobileAIAgentsPayloadProvider);
    final bootstrap = ref.watch(mobileBootstrapProvider).valueOrNull;
    final canManage = bootstrap?.can('can_manage_ai_agents') ?? false;

    return Scaffold(
      body: AppGradientBackground(
        child: SafeArea(
          child: RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(mobileAIAgentsPayloadProvider);
              await ref.read(mobileAIAgentsPayloadProvider.future);
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 112),
              children: [
                const BrandHeader(),
                const SizedBox(height: 24),
                _AIAgentsHero(canManage: canManage),
                const SizedBox(height: 18),
                TextField(
                  controller: _search,
                  onChanged: (_) => setState(() {}),
                  decoration: const InputDecoration(
                    hintText: 'Buscar agente, empresa o tipo',
                    prefixIcon: Icon(Icons.search_rounded),
                  ),
                ),
                const SizedBox(height: 18),
                payload.when(
                  loading: () => const SizedBox(
                      height: 260, child: AsyncStateView.loading()),
                  error: (_, __) => AsyncStateView.error(
                    'No pudimos cargar los agentes IA.',
                    actionLabel: 'Reintentar',
                    onAction: () =>
                        ref.invalidate(mobileAIAgentsPayloadProvider),
                  ),
                  data: (data) {
                    final agents = _filter(data.agents);
                    final active = data.agents
                        .where((agent) => agent['status'] == 'active')
                        .length;
                    final leads = data.agents.fold<int>(
                      0,
                      (sum, agent) => sum + _int(agent['lead_count']),
                    );
                    return Column(
                      children: [
                        _AIAgentsSummary(
                          total: data.agents.length,
                          active: active,
                          leads: leads,
                          dashboardUrl: data.dashboardUrl,
                          canManage: canManage,
                        ),
                        const SizedBox(height: 18),
                        GlassCard(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              SectionHeader(
                                title: 'Agentes IA',
                                actionLabel: canManage ? 'Panel' : null,
                                onAction: canManage &&
                                        data.dashboardUrl.isNotEmpty
                                    ? () =>
                                        NativeActions.website(data.dashboardUrl)
                                    : null,
                              ),
                              const SizedBox(height: 12),
                              if (agents.isEmpty)
                                AsyncStateView.empty(
                                  data.agents.isEmpty
                                      ? 'Sincroniza tus empresas para crear asistentes de negocio y agentes publicos.'
                                      : 'No hay agentes que coincidan con tu busqueda.',
                                  title: data.agents.isEmpty
                                      ? 'Sin agentes'
                                      : 'Sin resultados',
                                  icon: Icons.smart_toy_rounded,
                                  actionLabel:
                                      canManage ? 'Abrir panel IA' : null,
                                  onAction:
                                      canManage && data.dashboardUrl.isNotEmpty
                                          ? () => NativeActions.website(
                                              data.dashboardUrl)
                                          : null,
                                )
                              else
                                Column(
                                  children: [
                                    for (final agent in agents) ...[
                                      _AgentTile(
                                        agent: agent,
                                        canManageGlobal: canManage,
                                      ),
                                      const SizedBox(height: 12),
                                    ],
                                  ],
                                ),
                            ],
                          ),
                        ),
                      ],
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: null),
    );
  }

  List<Map<String, dynamic>> _filter(List<Map<String, dynamic>> agents) {
    final query = _search.text.trim().toLowerCase();
    if (query.isEmpty) return agents;
    return agents.where((agent) {
      final haystack = [
        agent['name'],
        agent['company_name'],
        agent['agent_type_label'],
        agent['mode_label'],
        agent['tone'],
      ].map(_text).join(' ').toLowerCase();
      return haystack.contains(query);
    }).toList();
  }
}

class _AIAgentsSummary extends StatelessWidget {
  const _AIAgentsSummary({
    required this.total,
    required this.active,
    required this.leads,
    required this.dashboardUrl,
    required this.canManage,
  });

  final int total;
  final int active;
  final int leads;
  final String dashboardUrl;
  final bool canManage;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(title: 'Centro de IA'),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: _MetricPill(
                  label: 'Agentes',
                  value: total.toString(),
                  icon: Icons.smart_toy_rounded,
                  color: AppColors.cyan,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _MetricPill(
                  label: 'Activos',
                  value: active.toString(),
                  icon: Icons.bolt_rounded,
                  color: AppColors.green,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _MetricPill(
                  label: 'Leads',
                  value: leads.toString(),
                  icon: Icons.person_add_alt_1_rounded,
                  color: AppColors.gold,
                ),
              ),
            ],
          ),
          if (canManage && dashboardUrl.isNotEmpty) ...[
            const SizedBox(height: 14),
            FilledButton.icon(
              onPressed: () => NativeActions.website(dashboardUrl),
              icon: const Icon(Icons.tune_rounded),
              label: const Text('Administrar agentes'),
            ),
          ],
        ],
      ),
    );
  }
}

class _AgentTile extends ConsumerWidget {
  const _AgentTile({
    required this.agent,
    required this.canManageGlobal,
  });

  final Map<String, dynamic> agent;
  final bool canManageGlobal;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final name = _text(agent['name'], fallback: 'Agente IA');
    final company = _text(agent['company_name'], fallback: 'Empresa');
    final type = _text(agent['agent_type_label'], fallback: 'Asistente');
    final mode = _text(agent['mode_label'], fallback: 'Reglas sin costo');
    final welcome = _text(agent['welcome_message'],
        fallback: 'Listo para responder con la informacion de la empresa.');
    final dashboardUrl = _text(agent['dashboard_url']);
    final status = _text(agent['status'], fallback: 'draft');
    final active = status == 'active';
    final suggestions = _items(agent['open_suggestions']);
    final questions = _strings(agent['suggested_questions']);
    final analytics = agent['analytics'] is Map<String, dynamic>
        ? agent['analytics'] as Map<String, dynamic>
        : const <String, dynamic>{};
    final agentId = _int(agent['id']);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.inkAlt.withValues(alpha: .72),
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(
          color: active
              ? AppColors.green.withValues(alpha: .32)
              : AppColors.gold.withValues(alpha: .32),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 54,
                height: 54,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [AppColors.purple, AppColors.blue],
                  ),
                  borderRadius: BorderRadius.circular(18),
                ),
                child: const Icon(Icons.smart_toy_rounded, color: Colors.white),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(name,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            fontSize: 17, fontWeight: FontWeight.w900)),
                    const SizedBox(height: 4),
                    Text('$company · $type',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            color: AppColors.muted, fontSize: 12)),
                  ],
                ),
              ),
              StatusBadge(
                label: active ? 'Activo' : 'Pausado',
                icon: active ? Icons.bolt_rounded : Icons.pause_rounded,
                color: active ? AppColors.green : AppColors.gold,
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(welcome,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: AppColors.muted, height: 1.4)),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: _TinyStat(
                    label: 'Base',
                    value: _text(agent['knowledge_count'], fallback: '0')),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _TinyStat(
                    label: 'FAQs',
                    value: _text(agent['faq_count'], fallback: '0')),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _TinyStat(
                    label: 'Leads',
                    value: _text(agent['lead_count'], fallback: '0')),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: _TinyStat(
                    label: 'Preguntas',
                    value: _text(analytics['questions'], fallback: '0')),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _TinyStat(
                    label: 'Sin respuesta',
                    value: _text(analytics['unanswered'], fallback: '0')),
              ),
              const SizedBox(width: 8),
              Expanded(child: _TinyStat(label: 'Modo', value: mode)),
            ],
          ),
          if (questions.isNotEmpty) ...[
            const SizedBox(height: 14),
            const Text('Preguntas sugeridas',
                style: TextStyle(fontWeight: FontWeight.w900, fontSize: 13)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final question in questions.take(4))
                  _QuestionChip(
                    question: question,
                    onTap: () => _testQuestion(context, ref, agentId, question),
                  ),
              ],
            ),
          ],
          if (suggestions.isNotEmpty) ...[
            const SizedBox(height: 14),
            _SuggestionsPreview(suggestions: suggestions),
          ],
          const SizedBox(height: 14),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              _ActionChipButton(
                label: 'Probar',
                icon: Icons.chat_bubble_rounded,
                enabled: agentId > 0,
                onTap: () => _showQuestionDialog(context, ref, agentId),
              ),
              _ActionChipButton(
                label: 'Panel',
                icon: Icons.tune_rounded,
                enabled: canManageGlobal && dashboardUrl.isNotEmpty,
                highlighted: true,
                onTap: () => NativeActions.website(dashboardUrl),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Future<void> _showQuestionDialog(
      BuildContext context, WidgetRef ref, int agentId) async {
    final controller = TextEditingController();
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: AppColors.panel,
        title: const Text('Probar agente'),
        content: TextField(
          controller: controller,
          autofocus: true,
          maxLines: 3,
          decoration: const InputDecoration(
            hintText: 'Escribe una pregunta para el agente',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.of(dialogContext).pop();
              _testQuestion(context, ref, agentId, controller.text);
            },
            child: const Text('Preguntar'),
          ),
        ],
      ),
    );
  }

  Future<void> _testQuestion(
      BuildContext context, WidgetRef ref, int agentId, String question) async {
    final cleanQuestion = question.trim();
    if (agentId <= 0 || cleanQuestion.isEmpty) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Consultando agente IA...')),
    );
    try {
      final result = await ref
          .read(mobileAIAgentsRepositoryProvider)
          .testQuestion(agentId, cleanQuestion);
      if (!context.mounted) return;
      showDialog<void>(
        context: context,
        builder: (_) => AlertDialog(
          backgroundColor: AppColors.panel,
          title: Text(_text(result['question'], fallback: cleanQuestion)),
          content: Text(
            _text(result['answer'], fallback: 'Sin respuesta disponible.'),
            style: const TextStyle(color: AppColors.muted, height: 1.45),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Cerrar'),
            ),
          ],
        ),
      );
    } catch (_) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No pudimos probar el agente.')),
      );
    }
  }
}

class _SuggestionsPreview extends StatelessWidget {
  const _SuggestionsPreview({required this.suggestions});

  final List<Map<String, dynamic>> suggestions;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.purple.withValues(alpha: .1),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.purple.withValues(alpha: .28)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Recomendaciones IA',
              style: TextStyle(
                  color: AppColors.purple, fontWeight: FontWeight.w900)),
          const SizedBox(height: 6),
          for (final suggestion in suggestions.take(3))
            Padding(
              padding: const EdgeInsets.only(bottom: 5),
              child: Text(
                _text(suggestion['title'], fallback: 'Recomendacion'),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: AppColors.muted, fontSize: 12),
              ),
            ),
        ],
      ),
    );
  }
}

class _QuestionChip extends StatelessWidget {
  const _QuestionChip({required this.question, required this.onTap});

  final String question;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(999),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: AppColors.panelSoft.withValues(alpha: .72),
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: AppColors.stroke),
        ),
        child: Text(question,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800)),
      ),
    );
  }
}

class _MetricPill extends StatelessWidget {
  const _MetricPill({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  final String label;
  final String value;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: .1),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: color.withValues(alpha: .26)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 8),
          Text(value,
              style:
                  const TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
          Text(label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: AppColors.muted, fontSize: 11)),
        ],
      ),
    );
  }
}

class _TinyStat extends StatelessWidget {
  const _TinyStat({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
      decoration: BoxDecoration(
        color: AppColors.panelSoft.withValues(alpha: .72),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.stroke),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(value,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontWeight: FontWeight.w900)),
          Text(label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: AppColors.muted, fontSize: 10)),
        ],
      ),
    );
  }
}

class _ActionChipButton extends StatelessWidget {
  const _ActionChipButton({
    required this.label,
    required this.icon,
    required this.onTap,
    this.enabled = true,
    this.highlighted = false,
  });

  final String label;
  final IconData icon;
  final VoidCallback onTap;
  final bool enabled;
  final bool highlighted;

  @override
  Widget build(BuildContext context) {
    final color = highlighted ? AppColors.purple : AppColors.text;
    return InkWell(
      onTap: enabled ? onTap : null,
      borderRadius: BorderRadius.circular(999),
      child: Opacity(
        opacity: enabled ? 1 : .42,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 10),
          decoration: BoxDecoration(
            color: highlighted
                ? AppColors.purple.withValues(alpha: .2)
                : AppColors.panelSoft.withValues(alpha: .75),
            borderRadius: BorderRadius.circular(999),
            border: Border.all(color: color.withValues(alpha: .28)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 16, color: color),
              const SizedBox(width: 6),
              Text(label,
                  style: TextStyle(color: color, fontWeight: FontWeight.w900)),
            ],
          ),
        ),
      ),
    );
  }
}

class _AIAgentsHero extends StatelessWidget {
  const _AIAgentsHero({required this.canManage});

  final bool canManage;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      gradient: AppGradients.cardGlow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          StatusBadge(
            label: canManage ? 'IA habilitada' : 'Vista de agentes',
            icon: Icons.smart_toy_rounded,
            color: canManage ? AppColors.green : AppColors.gold,
          ),
          const SizedBox(height: 16),
          const Text('Agentes IA',
              style: TextStyle(
                  fontSize: 32, height: 1.05, fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          const Text(
            'Administra asistentes de negocio, guias y agentes publicos sin depender de servicios pagados externos.',
            style: TextStyle(color: AppColors.muted, height: 1.45),
          ),
        ],
      ),
    );
  }
}

List<Map<String, dynamic>> _items(dynamic value) {
  if (value is! List) return const <Map<String, dynamic>>[];
  return value.whereType<Map<String, dynamic>>().toList();
}

List<String> _strings(dynamic value) {
  if (value is! List) return const <String>[];
  return value
      .map((item) => item.toString())
      .where((item) => item.isNotEmpty)
      .toList();
}

String _text(dynamic value, {String fallback = ''}) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
}

int _int(dynamic value) {
  if (value is int) return value;
  return int.tryParse(value?.toString() ?? '') ?? 0;
}
