/// === INTEGRATION STUB: plugin_infrastructure.dart ===
///
/// This file demonstrates how to register the Vault Browser as an
/// AppFlowy-LAI style plugin in `lib/plugins/plugin_infrastructure.dart`
/// (or the equivalent plugin registry in your AppFlowy checkout).
///
/// Copy the relevant class into your plugin registry and ensure the
/// `vault_browser_plugin` package is listed as a dependency in
/// `pubspec.yaml`.
///
/// ---------------------------------------------------------------------------

// ----- ADD THIS IMPORT at the top of the registry file -----

// import 'package:vault_browser_plugin/vault_browser_plugin.dart';

// ----- ADD THIS CLASS to the plugin registry -----

// /// Plugin that adds a vault workspace switcher and "All Docs" browser
// /// to the AppFlowy home sidebar.
// class VaultBrowserPlugin extends AppFlowyPlugin {
//   @override
//   String get id => 'vault_browser';
//
//   @override
//   String get displayName => 'Vault Browser';
//
//   @override
//   String get description =>
//       'Browse and switch between User, Shared, and Public vault workspaces '
//       'with a full-text searchable document browser.';
//
//   @override
//   PluginType get type => PluginType.sidebar;
//
//   @override
//   Widget? buildSidebarWidget(BuildContext context) {
//     return BlocProvider(
//       create: (_) => VaultSwitcherBloc()..add(const LoadVaultsEvent()),
//       child: VaultSwitcherWidget(
//         onVaultChanged: (vault) {
//           // Delegate vault switch to the host sidebar.
//           // In a real integration, you'd emit a global event here.
//         },
//       ),
//     );
//   }
//
//   @override
//   Widget? buildPageWidget(BuildContext context, String pageId) {
//     // Return a DocBrowserWidget for the "All Docs" tab.
//     if (pageId == 'all_docs') {
//       return BlocProvider(
//         create: (_) => DocBrowserBloc(),
//         child: DocBrowserWidget(
//           onDocOpened: (doc) {
//             // Delegate doc-open to the host.
//           },
//         ),
//       );
//     }
//     return null;
//   }
// }

// ----- REGISTER THE PLUGIN in the plugin callback list -----

// // In the plugin registry's init or main function:
// void registerVaultBrowserPlugin(PluginRegistry registry) {
//   registry.register(VaultBrowserPlugin());
// }

// ----- OPTIONAL: Menu entry registration -----

// /// Register a menu item that opens "All Docs" as a new tab.
// void registerAllDocsMenuEntry(MenuRegistry menu) {
//   menu.addItem(MenuItem.sidebar(
//     id: 'all_docs',
//     label: '📚 All Docs',
//     icon: Icons.folder_open_rounded,
//     onTap: (context) {
//       // Open DocBrowserWidget as a new tab.
//       // context.read<TabsBloc>().add(TabsEvent.openTab(...));
//     },
//   ));
// }