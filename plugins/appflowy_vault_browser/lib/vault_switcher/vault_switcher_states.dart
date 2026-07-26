/// States for the Vault Switcher BLoC.
library vault_switcher_states;

import 'vault_switcher_events.dart';

/// A single vault entry displayed in the switcher.
class VaultInfo {
  final String name;
  final String path;
  final String vaultType; // 'user', 'shared', 'public'
  final String icon;

  const VaultInfo({
    required this.name,
    required this.path,
    required this.vaultType,
    required this.icon,
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is VaultInfo &&
          runtimeType == other.runtimeType &&
          name == other.name &&
          path == other.path;

  @override
  int get hashCode => name.hashCode ^ path.hashCode;

  @override
  String toString() => 'VaultInfo(name: $name, path: $path, type: $vaultType)';
}

/// Base class for vault switcher states.
abstract class VaultSwitcherState {
  const VaultSwitcherState();
}

/// Initial state before any vaults are loaded.
class VaultSwitcherInitial extends VaultSwitcherState {
  const VaultSwitcherInitial();
}

/// Vaults are currently being discovered.
class VaultSwitcherLoading extends VaultSwitcherState {
  const VaultSwitcherLoading();
}

/// Vaults have been loaded successfully.
class VaultSwitcherLoaded extends VaultSwitcherState {
  final List<VaultInfo> vaults;
  final VaultInfo? activeVault;

  const VaultSwitcherLoaded({
    required this.vaults,
    this.activeVault,
  });

  @override
  String toString() =>
      'VaultSwitcherLoaded(vaults: ${vaults.length}, active: $activeVault)';
}

/// A vault switch is in progress.
class VaultSwitcherSwitching extends VaultSwitcherState {
  final VaultInfo targetVault;

  const VaultSwitcherSwitching({required this.targetVault});

  @override
  String toString() =>
      'VaultSwitcherSwitching(target: ${targetVault.name})';
}

/// Failed to load or switch vaults.
class VaultSwitcherError extends VaultSwitcherState {
  final String message;

  const VaultSwitcherError({required this.message});

  @override
  String toString() => 'VaultSwitcherError($message)';
}