/// Barrel export for the AppFlowy Vault Browser plugin.
///
/// This plugin provides:
///   - [VaultSwitcherWidget] — A dropdown to switch between User, Shared,
///     and Public vaults (~/Vault, ~/Shared/*, ~/Public/*).
///   - [DocBrowserWidget] — A searchable "All Docs" browser that shows
///     every document in the active vault.
///
/// ## Integration Quick-Start
///
/// ### 1. Add the vault switcher to the home sidebar
///
/// In `lib/plugins/home/home_sidebar.dart`, wrap the sidebar body:
///
/// ```dart
/// import 'package:vault_browser_plugin/vault_browser_plugin.dart';
///
/// // Inside HomeSideBarState:
/// Widget build(BuildContext context) {
///   return MultiBlocProvider(
///     providers: [
///       BlocProvider(create: (_) => VaultSwitcherBloc()),
///       BlocProvider(create: (_) => DocBrowserBloc()),
///     ],
///     child: Column(
///       children: [
///         VaultSwitcherWidget(
///           onVaultChanged: (vault) {
///             // Switch AppFlowy workspace:
///             // context.read<TabsBloc>().add(TabsEvent.switchWorkspace(vault.path));
///             // Reload sidebar and doc browser:
///             // DocBrowserWidget.loadVault(context, vault.path);
///           },
///         ),
///         // ... existing sidebar items ...
///         ListTile(
///           leading: const Icon(Icons.folder_open),
///           title: const Text('All Docs'),
///           onTap: () => _openAllDocsTab(context),
///         ),
///       ],
///     ),
///   );
/// }
///
/// void _openAllDocsTab(BuildContext context) {
///   // Open the DocBrowserWidget as a new tab:
///   // context.read<TabsBloc>().add(TabsEvent.openTab(TabInfo(
///   //   label: 'All Docs',
///   //   icon: Icons.folder_open,
///   //   widget: const DocBrowserWidget(
///   //     onDocOpened: (doc) { ... open doc via TabsEvent ... },
///   //   ),
///   // )));
/// }
/// ```
///
/// ### 2. Register the plugin
///
/// In `lib/plugins/plugin_infrastructure.dart` (or equivalent):
///
/// ```dart
/// import 'package:vault_browser_plugin/vault_browser_plugin.dart';
///
/// class VaultBrowserPlugin extends AppFlowyPlugin {
///   @override
///   String get id => 'vault_browser';
///
///   @override
///   Widget buildSidebarWidget() => const VaultSwitcherWidget();
/// }
/// ```
library vault_browser_plugin;

// Vault Switcher
export 'vault_switcher/vault_switcher_bloc.dart';
export 'vault_switcher/vault_switcher_events.dart';
export 'vault_switcher/vault_switcher_states.dart';
export 'vault_switcher/vault_switcher_widget.dart';

// Document Browser
export 'doc_browser/doc_browser_bloc.dart';
export 'doc_browser/doc_browser_events.dart';
export 'doc_browser/doc_browser_states.dart';
export 'doc_browser/doc_browser_widget.dart';