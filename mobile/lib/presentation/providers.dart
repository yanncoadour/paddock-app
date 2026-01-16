import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'package:paddock/data/repositories/auth_repository.dart';
import 'package:paddock/data/repositories/gp_repository.dart';
import 'package:paddock/data/repositories/paddock_repository.dart';
import 'package:paddock/data/repositories/standings_repository.dart';
import 'package:paddock/data/storage/token_storage.dart';
import 'package:paddock/domain/models/grand_prix.dart';
import 'package:paddock/domain/models/grand_prix_detail.dart';
import 'package:paddock/domain/models/paddock.dart';
import 'package:paddock/domain/models/season.dart';
import 'package:paddock/domain/models/standing.dart';
import 'package:paddock/domain/models/user.dart';

final tokenStorageProvider = Provider<TokenStorage>((ref) {
  const storage = FlutterSecureStorage();
  return TokenStorage(storage);
});

class AuthController extends StateNotifier<AsyncValue<User?>> {
  AuthController(this._repository, this._tokenStorage) : super(const AsyncLoading());

  final AuthRepository _repository;
  final TokenStorage _tokenStorage;

  Future<void> bootstrap() async {
    final token = await _tokenStorage.readToken();
    if (token == null || token.isEmpty) {
      state = const AsyncData(null);
      return;
    }
    try {
      final user = await _repository.fetchMe();
      state = AsyncData(user);
    } catch (_) {
      await _tokenStorage.clearToken();
      state = const AsyncData(null);
    }
  }

  Future<void> login(String email, String password) async {
    state = const AsyncLoading();
    await _repository.login(email: email, password: password);
    final user = await _repository.fetchMe();
    state = AsyncData(user);
  }

  Future<void> register(String email, String password, String displayName) async {
    state = const AsyncLoading();
    await _repository.register(email: email, password: password, displayName: displayName);
    final user = await _repository.fetchMe();
    state = AsyncData(user);
  }

  Future<void> logout() async {
    await _repository.logout();
    state = const AsyncData(null);
  }

  void reset() {
    state = const AsyncData(null);
  }
}

final authControllerProvider = StateNotifierProvider<AuthController, AsyncValue<User?>>((ref) {
  final repository = ref.watch(authRepositoryProvider);
  final tokenStorage = ref.watch(tokenStorageProvider);
  return AuthController(repository, tokenStorage);
});

final authStateProvider = Provider<AsyncValue<User?>>((ref) {
  return ref.watch(authControllerProvider);
});

final authStateStreamProvider = Provider<Stream<AsyncValue<User?>>>((ref) {
  return ref.watch(authControllerProvider.notifier).stream;
});

final currentUserProvider = Provider<User?>((ref) {
  final auth = ref.watch(authControllerProvider);
  return auth.valueOrNull;
});

final currentSeasonProvider = FutureProvider<Season>((ref) async {
  final repo = ref.watch(gpRepositoryProvider);
  return repo.fetchCurrentSeason();
});

final gpsProvider = FutureProvider.family<List<GrandPrix>, int>((ref, seasonYear) async {
  final repo = ref.watch(gpRepositoryProvider);
  return repo.fetchGrandPrix(seasonYear);
});

final gpDetailProvider = FutureProvider.family<GrandPrixDetail, int>((ref, gpId) async {
  final repo = ref.watch(gpRepositoryProvider);
  return repo.fetchGrandPrixDetail(gpId);
});

final paddocksProvider = FutureProvider<List<Paddock>>((ref) async {
  final repo = ref.watch(paddockRepositoryProvider);
  return repo.fetchPaddocks();
});

final paddockDetailProvider = FutureProvider.family<Paddock, int>((ref, paddockId) async {
  final repo = ref.watch(paddockRepositoryProvider);
  return repo.fetchPaddock(paddockId);
});

final gpStandingsProvider = FutureProvider.family<List<Standing>, int>((ref, gpId) async {
  final repo = ref.watch(standingsRepositoryProvider);
  return repo.fetchGpStandings(gpId);
});

final seasonStandingsProvider = FutureProvider.family<List<Standing>, ({int seasonId, int paddockId})>((ref, args) async {
  final repo = ref.watch(standingsRepositoryProvider);
  return repo.fetchSeasonStandings(seasonId: args.seasonId, paddockId: args.paddockId);
});
