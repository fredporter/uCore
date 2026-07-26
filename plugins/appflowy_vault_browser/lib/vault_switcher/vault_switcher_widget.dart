/// Vault Switcher dropdown widget.
///
/// Renders a themed dropdown at the top of the sidebar showing all
/// discovered vaults (User, Shared, Public). Emits [SwitchVaultEvent]
/// when the user selects a different vault.
library vault_switcher_widget;

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'vault_switcher_bloc.dart';
import 'vault_switcher_events.dart';
import 'vault_switcher_states.dart';

/// Dropdown widget for selecting the active vault.
///
/// Place this at the top of the home sidebar. It auto-loads vaults
/// on mount and stays in sync with the [VaultSwitcherBloc].
///
/// Usage:
/// ```dart
/// BlocProvider(
///   create: (_) => VaultSwitcherBloc()..add(const LoadVaultsEvent()),
///   child: const VaultSwitcherWidget(),
/// )
/// ```
class VaultSwitcherWidget extends StatefulWidget {
  /// Callback fired when the user selects a vault.
  /// Receives the selected [VaultInfo].
  final void Function(VaultInfo vault)? onVaultChanged;

  const VaultSwitcherWidget({
    super.key,
    this.onVaultChanged,
  });

  @override
  State<VaultSwitcherWidget> createState() => _VaultSwitcherWidgetState();
}

class _VaultSwitcherWidgetState extends State<VaultSwitcherWidget> {
  @override
  void initState() {
    super.initState();
    // Trigger initial vault discovery if not already loaded.
    final bloc = context.read<VaultSwitcherBloc>();
    if (bloc.state is VaultSwitcherInitial) {
      bloc.add(const LoadVaultsEvent());
    }
  }

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<VaultSwitcherBloc, VaultSwitcherState>(
      listener: _onStateChanged,
      builder: (context, state) => _buildContent(context, state),
    );
  }

  void _onStateChanged(BuildContext context, VaultSwitcherState state) {
    if (state is VaultSwitcherLoaded && state.activeVault != null) {
      widget.onVaultChanged?.call(state.activeVault!);
    }
    if (state is VaultSwitcherError) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(state.message),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  Widget _buildContent(BuildContext context, VaultSwitcherState state) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      child: _buildDropdown(context, state),
    );
  }

  Widget _buildDropdown(BuildContext context, VaultSwitcherState state) {
    final isEnabled = state is VaultSwitcherLoaded;
    final activeVault =
        state is VaultSwitcherLoaded ? state.activeVault : null;
    final vaults = state is VaultSwitcherLoaded ? state.vaults : <VaultInfo>[];
    final isLoading = state is VaultSwitcherLoading ||
        state is VaultSwitcherSwitching;

    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: Theme.of(context)
              .colorScheme
              .outline
              .withValues(alpha: 0.2),
        ),
        color: Theme.of(context)
            .colorScheme
            .surfaceContainerHighest
            .withValues(alpha: 0.4),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<VaultInfo>(
          value: activeVault,
          isExpanded: true,
          isDense: true,
          icon: isLoading
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.expand_more, size: 20),
          hint: Text(
            isLoading ? 'Scanning vaults…' : 'Select Vault',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          onChanged: isEnabled
              ? (vault) {
                  if (vault == null) return;
                  context.read<VaultSwitcherBloc>().add(
                        SwitchVaultEvent(
                          vaultPath: vault.path,
                          vaultName: vault.name,
                        ),
                      );
                }
              : null,
          selectedItemBuilder: (context) {
            return vaults.map<Widget>((v) {
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Row(
                  children: [
                    Text(v.icon, style: const TextStyle(fontSize: 16)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        v.name,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.w600,
                            ),
                      ),
                    ),
                  ],
                ),
              );
            }).toList();
          },
          items: vaults.map<DropdownMenuItem<VaultInfo>>((vault) {
            return DropdownMenuItem<VaultInfo>(
              value: vault,
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: _VaultListTile(vault: vault),
              ),
            );
          }).toList(),
        ),
      ),
    );
  }
}

/// Row displaying vault icon, name, and type badge.
class _VaultListTile extends StatelessWidget {
  final VaultInfo vault;

  const _VaultListTile({required this.vault});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      child: Row(
        children: [
          Text(vault.icon, style: const TextStyle(fontSize: 18)),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              vault.name,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(4),
              color: _badgeColor(context).withValues(alpha: 0.12),
            ),
            child: Text(
              vault.vaultType.toUpperCase(),
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: _badgeColor(context),
                    fontWeight: FontWeight.w700,
                    fontSize: 10,
                    letterSpacing: 0.5,
                  ),
            ),
          ),
        ],
      ),
    );
  }

  Color _badgeColor(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    switch (vault.vaultType) {
      case 'user':
        return scheme.primary;
      case 'shared':
        return scheme.tertiary;
      case 'public':
        return scheme.secondary;
      default:
        return scheme.onSurfaceVariant;
    }
  }
}