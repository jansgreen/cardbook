import 'package:go_router/go_router.dart';
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
import 'package:mobile_cardbook/features/home/presentation/home_screen.dart';
import 'package:mobile_cardbook/features/jobs/presentation/jobs_screen.dart';
import 'package:mobile_cardbook/features/notifications/presentation/notifications_screen.dart';
import 'package:mobile_cardbook/features/profile/presentation/profile_edit_screen.dart';
import 'package:mobile_cardbook/features/profile/presentation/profile_screen.dart';
import 'package:mobile_cardbook/features/websites/presentation/websites_screen.dart';

final appRouter = GoRouter(
  initialLocation: '/login',
  routes: [
    GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
    GoRoute(path: '/register', builder: (context, state) => const RegisterScreen()),
    GoRoute(path: '/', builder: (context, state) => const HomeScreen()),
    GoRoute(path: '/companies', builder: (context, state) => const CompaniesScreen()),
    GoRoute(
      path: '/companies/form',
      builder: (context, state) => CompanyFormScreen(
        company: state.extra is Map<String, dynamic> ? state.extra as Map<String, dynamic> : null,
      ),
    ),
    GoRoute(
      path: '/companies/detail',
      builder: (context, state) => CompanyDetailScreen(
        company: state.extra is Map<String, dynamic> ? state.extra as Map<String, dynamic> : const <String, dynamic>{},
      ),
    ),
    GoRoute(path: '/cards', builder: (context, state) => const CardsScreen()),
    GoRoute(
      path: '/cards/digital/form',
      builder: (context, state) => DigitalCardFormScreen(
        card: state.extra is Map<String, dynamic> ? state.extra as Map<String, dynamic> : null,
      ),
    ),
    GoRoute(
      path: '/cards/business/form',
      builder: (context, state) => BusinessCardFormScreen(
        card: state.extra is Map<String, dynamic> ? state.extra as Map<String, dynamic> : null,
      ),
    ),
    GoRoute(
      path: '/cards/detail',
      builder: (context, state) {
        final extra = state.extra is Map<String, dynamic> ? state.extra as Map<String, dynamic> : const <String, dynamic>{};
        final card = extra['card'] is Map<String, dynamic> ? extra['card'] as Map<String, dynamic> : const <String, dynamic>{};
        final kind = extra['kind']?.toString() ?? 'digital';
        return CardDetailScreen(card: card, kind: kind);
      },
    ),
    GoRoute(path: '/book', builder: (context, state) => const BookScreen()),
    GoRoute(path: '/jobs', builder: (context, state) => const JobsScreen()),
    GoRoute(path: '/websites', builder: (context, state) => const WebsitesScreen()),
    GoRoute(path: '/notifications', builder: (context, state) => const NotificationsScreen()),
    GoRoute(path: '/profile', builder: (context, state) => const ProfileScreen()),
    GoRoute(
      path: '/profile/edit',
      builder: (context, state) => ProfileEditScreen(
        profile: state.extra is Map<String, dynamic> ? state.extra as Map<String, dynamic> : null,
      ),
    ),
  ],
);
