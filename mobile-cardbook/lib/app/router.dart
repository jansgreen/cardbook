import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/alliances/presentation/alliances_screen.dart';
import 'package:mobile_cardbook/features/auth/presentation/login_screen.dart';
import 'package:mobile_cardbook/features/auth/presentation/register_screen.dart';
import 'package:mobile_cardbook/features/book/presentation/book_screen.dart';
import 'package:mobile_cardbook/features/cards/presentation/business_card_form_screen.dart';
import 'package:mobile_cardbook/features/cards/presentation/card_detail_screen.dart';
import 'package:mobile_cardbook/features/cards/presentation/cards_screen.dart';
import 'package:mobile_cardbook/features/cards/presentation/digital_card_form_screen.dart';
import 'package:mobile_cardbook/features/companies/presentation/company_detail_screen.dart';
import 'package:mobile_cardbook/features/companies/presentation/company_form_screen.dart';
import 'package:mobile_cardbook/features/companies/presentation/companies_screen.dart';
import 'package:mobile_cardbook/features/diagnostics/presentation/diagnostics_screen.dart';
import 'package:mobile_cardbook/features/home/presentation/home_screen.dart';
import 'package:mobile_cardbook/features/jobs/presentation/job_form_screen.dart';
import 'package:mobile_cardbook/features/jobs/presentation/jobs_screen.dart';
import 'package:mobile_cardbook/features/marketplace/presentation/marketplace_screen.dart';
import 'package:mobile_cardbook/features/notifications/presentation/notifications_screen.dart';
import 'package:mobile_cardbook/features/profile/presentation/profile_edit_screen.dart';
import 'package:mobile_cardbook/features/profile/presentation/profile_screen.dart';
import 'package:mobile_cardbook/features/support/presentation/support_screen.dart';
import 'package:mobile_cardbook/features/websites/presentation/websites_screen.dart';

final appRouter = GoRouter(
  initialLocation: '/login',
  routes: [
    GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
    GoRoute(
        path: '/register', builder: (context, state) => const RegisterScreen()),
    GoRoute(path: '/', builder: (context, state) => const HomeScreen()),
    GoRoute(
        path: '/companies',
        builder: (context, state) => const CompaniesScreen()),
    GoRoute(
      path: '/companies/form',
      builder: (context, state) => CompanyFormScreen(
        company: state.extra is Map<String, dynamic>
            ? state.extra as Map<String, dynamic>
            : null,
      ),
    ),
    GoRoute(
      path: '/companies/detail',
      builder: (context, state) => CompanyDetailScreen(
        company: state.extra is Map<String, dynamic>
            ? state.extra as Map<String, dynamic>
            : const <String, dynamic>{},
      ),
    ),
    GoRoute(path: '/cards', builder: (context, state) => const CardsScreen()),
    GoRoute(
      path: '/cards/digital/form',
      builder: (context, state) {
        final extra = state.extra is Map<String, dynamic>
            ? state.extra as Map<String, dynamic>
            : const <String, dynamic>{};
        return DigitalCardFormScreen(
          card: extra.isEmpty || extra.containsKey('initialCompany')
              ? null
              : extra,
          initialCompany: extra['initialCompany'] is Map<String, dynamic>
              ? extra['initialCompany'] as Map<String, dynamic>
              : null,
        );
      },
    ),
    GoRoute(
      path: '/cards/business/form',
      builder: (context, state) {
        final extra = state.extra is Map<String, dynamic>
            ? state.extra as Map<String, dynamic>
            : const <String, dynamic>{};
        return BusinessCardFormScreen(
          card: extra.isEmpty || extra.containsKey('initialCompany')
              ? null
              : extra,
          initialCompany: extra['initialCompany'] is Map<String, dynamic>
              ? extra['initialCompany'] as Map<String, dynamic>
              : null,
        );
      },
    ),
    GoRoute(
      path: '/cards/detail',
      builder: (context, state) {
        final extra = state.extra is Map<String, dynamic>
            ? state.extra as Map<String, dynamic>
            : const <String, dynamic>{};
        final card = extra['card'] is Map<String, dynamic>
            ? extra['card'] as Map<String, dynamic>
            : const <String, dynamic>{};
        final kind = extra['kind']?.toString() ?? 'digital';
        return CardDetailScreen(card: card, kind: kind);
      },
    ),
    GoRoute(path: '/book', builder: (context, state) => const BookScreen()),
    GoRoute(
        path: '/marketplace',
        builder: (context, state) => const MarketplaceScreen()),
    GoRoute(path: '/jobs', builder: (context, state) => const JobsScreen()),
    GoRoute(
      path: '/jobs/form',
      builder: (context, state) => JobFormScreen(
        job: state.extra is Map<String, dynamic>
            ? state.extra as Map<String, dynamic>
            : null,
      ),
    ),
    GoRoute(
        path: '/websites', builder: (context, state) => const WebsitesScreen()),
    GoRoute(
        path: '/notifications',
        builder: (context, state) => const NotificationsScreen()),
    GoRoute(
        path: '/alliances',
        builder: (context, state) => const AlliancesScreen()),
    GoRoute(
        path: '/profile', builder: (context, state) => const ProfileScreen()),
    GoRoute(
        path: '/diagnostics',
        builder: (context, state) => const DiagnosticsScreen()),
    GoRoute(
        path: '/support', builder: (context, state) => const SupportScreen()),
    GoRoute(
      path: '/profile/edit',
      builder: (context, state) => ProfileEditScreen(
        profile: state.extra is Map<String, dynamic>
            ? state.extra as Map<String, dynamic>
            : null,
      ),
    ),
  ],
);
