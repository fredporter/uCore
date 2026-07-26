/// Events for the Vault Switcher BLoC.
library vault_switcher_events;

/// Base class for all vault switcher events.
abstract class VaultSwitcherEvent {
  const VaultSwitcherEvent();
}

/// Request to load all available vaults from the filesystem.
class LoadVaultsEvent extends VaultSwitcherEvent {
  const LoadVaultsEvent();
}

/// User selected a vault from the switcher dropdown.
class SwitchVaultEvent extends VaultSwitcherEvent {
  final String vaultPath;
  final String vaultName;

  const SwitchVaultEvent({
    required this.vaultPath,
    required this.vaultName,
  });

  @override
  String toString() => 'SwitchVaultEvent(path: $vaultPath, name: $vaultName)';
}