import 'package:go_router/go_router.dart';
import 'package:mobile_cardbook/features/auth/presentation/login_screen.dart';
import 'package:mobile_cardbook/features/book/presentation/book_screen.dart';
import 'package:mobile_cardbook/features/cards/presentation/cards_screen.dart';
import 'package:mobile_cardbook/features/companies/presentation/companies_screen.dart';
import 'package:mobile_cardbook/features/home/presentation/home_screen.dart';
import 'package:mobile_cardbook/features/notifications/presentation/notifications_screen.dart';

final appRouter = GoRouter(
  initialLocation: '/login',
  routes: [
    GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
    GoRoute(path: '/', builder: (context, state) => const HomeScreen()),
    GoRoute(path: '/companies', builder: (context, state) => const CompaniesScreen()),
    GoRoute(path: '/cards', builder: (context, state) => const CardsScreen()),
    GoRoute(path: '/book', builder: (context, state) => const BookScreen()),
    GoRoute(path: '/notifications', builder: (context, state) => const NotificationsScreen()),
  ],
);
