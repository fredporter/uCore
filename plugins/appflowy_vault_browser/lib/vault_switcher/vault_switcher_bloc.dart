/// BLoC for managing vault discovery and switching.
library vault_switcher_bloc;

import 'dart:async';
import 'dart:io';

import 'package:flutter_bloc/flutter_bloc.dart';

import 'vault_switcher_events.dart';
import 'vault_switcher_states.dart';

/// Discovers vault directories on the local filesystem and manages
/// switching between them.
///
/// Vaults are organised in three categories:
///   - User Vault: ~/Vault (personal workspace)
///   - Shared Vaults: subdirectories of ~/Shared/
///   - Public Vaults: subdirectories of ~/Public/
class VaultSwitcherBloc extends Bloc<VaultSwitcherEvent, VaultSwitcherState> {
  VaultSwitcherBloc() : super(const VaultSwitcherInitial()) {
    on<LoadVaultsEvent>(_onLoadVaults);
    on<SwitchVaultEvent>(_onSwitchVault);
  }

  /// Canonical home directory for vault resolution.
  static String get _homeDir {
    final envHome = Platform.environment['HOME'];
    if (envHome != null && envHome.isNotEmpty) return envHome;
    // Fallback: compose from platform paths
    if (Platform.isMacOS || Platform.isLinux) {
      return '/Users/${Platform.environment['USER'] ?? 'user'}';
    }
    return Platform.environment['USERPROFILE'] ??
        'C:\\Users\\${Platform.environment['USERNAME'] ?? 'user'}';
  }

  Future<void> _onLoadVaults(
    LoadVaultsEvent event,
    Emitter<VaultSwitcherState> emit,
  ) async {
    emit(const VaultSwitcherLoading());

    try {
      final vaults = await _discoverVaults();

      if (vaults.isEmpty) {
        emit(const VaultSwitcherError(
          message: 'No vaults found. Ensure ~/Vault, ~/Shared, '
              'and ~/Public directories exist.',
        ));
        return;
      }

      // Default active vault is the User Vault if available.
      final activeVault = vaults.firstWhere(
        (v) => v.vaultType == 'user',
        orElse: () => vaults.first,
      );

      emit(VaultSwitcherLoaded(vaults: vaults, activeVault: activeVault));
    } catch (e) {
      emit(VaultSwitcherError(message: 'Failed to discover vaults: $e'));
    }
  }

  Future<void> _onSwitchVault(
    SwitchVaultEvent event,
    Emitter<VaultSwitcherState> emit,
  ) async {
    final currentState = state;
    if (currentState is! VaultSwitcherLoaded) return;

    final target = currentState.vaults.firstWhere(
      (v) => v.path == event.vaultPath,
      orElse: () => VaultInfo(
        name: event.vaultName,
        path: event.vaultPath,
        vaultType: 'unknown',
        icon: '📁',
      ),
    );

    emit(VaultSwitcherSwitching(targetVault: target));

    try {
      // Verify the directory is accessible.
      final dir = Directory(target.path);
      final exists = await dir.exists();
      if (!exists) {
        emit(VaultSwitcherError(
          message: 'Vault directory not found: ${target.path}',
        ));
        // Re-emit loaded state so UI doesn't lock up.
        emit(currentState);
        return;
      }

      emit(VaultSwitcherLoaded(
        vaults: currentState.vaults,
        activeVault: target,
      ));
    } catch (e) {
      emit(VaultSwitcherError(message: 'Failed to switch vault: $e'));
      emit(currentState);
    }
  }

  /// Walk ~/Vault, ~/Shared/*, ~/Public/* and return [VaultInfo] entries.
  Future<List<VaultInfo>> _discoverVaults() async {
    final results = <VaultInfo>[];
    final home = Directory(_homeDir);

    // --- User Vault ---
    final userVault = Directory('${home.path}/Vault');
    if (await userVault.exists()) {
      results.add(const VaultInfo(
        name: 'User Vault',
        path: '~/Vault',
        vaultType: 'user',
        icon: '🏠',
      ));
    }

    // --- Shared Vaults ---
    final sharedDir = Directory('${home.path}/Shared');
    if (await sharedDir.exists()) {
      await for (final entity in sharedDir.list()) {
        if (entity is Directory) {
          final dirName = entity.path.split(Platform.pathSeparator).last;
          // Skip hidden directories.
          if (dirName.startsWith('.')) continue;
          results.add(VaultInfo(
            name: 'Shared: $dirName',
            path: '~/Shared/$dirName',
            vaultType: 'shared',
            icon: '👥',
          ));
        }
      }
    }

    // --- Public Vaults ---
    final publicDir = Directory('${home.path}/Public');
    if (await publicDir.exists()) {
      await for (final entity in publicDir.list()) {
        if (entity is Directory) {
          final dirName = entity.path.split(Platform.pathSeparator).last;
          if (dirName.startsWith('.')) continue;
          results.add(VaultInfo(
            name: 'Public: $dirName',
            path: '~/Public/$dirName',
            vaultType: 'public',
            icon: '🌐',
          ));
        }
      }
    }

    return results;
  }
}