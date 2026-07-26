/// === INTEGRATION STUB: home_sidebar.dart ===
///
/// This file demonstrates how to integrate [VaultSwitcherWidget] and the
/// "All Docs" entry into AppFlowy's existing `home_sidebar.dart`.
///
/// Copy the relevant sections into:
///   lib/plugins/home/home_sidebar.dart
///
/// Key changes:
///   1. Add BLoC providers above the sidebar body.
///   2. Insert [VaultSwitcherWidget] at the top of the sidebar.
///   3. Add an "All Docs" [ListTile] that opens [DocBrowserWidget] in a tab.
///
/// ---------------------------------------------------------------------------

// ----- ADD THESE IMPORTS at the top of home_sidebar.dart -----

import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:vault_browser_plugin/vault_browser_plugin.dart';
// import 'package:appflowy/plugins/tabs/tabs_bloc.dart';          // adjust to actual path
// import 'package:appflowy/plugins/tabs/tabs_event.dart';         // adjust to actual path

// ----- ADD THESE MEMBERS to HomeSideBarState -----

// /// BLoCs scoped to the sidebar lifecycle.
// late final VaultSwitcherBloc _vaultSwitcherBloc;
// late final DocBrowserBloc _docBrowserBloc;
//
// @override
// void initState() {
//   super.initState();
//   _vaultSwitcherBloc = VaultSwitcherBloc()..add(const LoadVaultsEvent());
//   _docBrowserBloc = DocBrowserBloc();
// }
//
// @override
// void dispose() {
//   _vaultSwitcherBloc.close();
//   _docBrowserBloc.close();
//   super.dispose();
// }

// ----- WRAP THE SIDEBAR BODY in MultiBlocProvider -----

// Inside `HomeSideBar.build()`:
//
// @override
// Widget build(BuildContext context) {
//   return MultiBlocProvider(
//     providers: [
//       BlocProvider.value(value: _vaultSwitcherBloc),
//       BlocProvider.value(value: _docBrowserBloc),
//     ],
//     child: Container(
//       // ... existing sidebar container ...
//       child: Column(
//         children: [
//           // ─── VAULT SWITCHER ───
//           VaultSwitcherWidget(
//             onVaultChanged: _onVaultChanged,
//           ),
//           const Divider(height: 1),
//
//           // ─── "ALL DOCS" ENTRY ───
//           _buildAllDocsEntry(context),
//           const Divider(height: 1),
//
//           // ... existing sidebar items (workspace tree, etc.) ...
//         ],
//       ),
//     ),
//   );
// }

// ----- ADD THESE METHODS to HomeSideBarState -----

// /// Called when the user selects a vault in the dropdown.
// void _onVaultChanged(VaultInfo vault) {
//   // 1. Tell AppFlowy to switch workspaces.
//   //    Adjust `switchWorkspace` to match the actual TabsBloc API.
//   // context.read<TabsBloc>().add(TabsEvent.switchWorkspace(vault.path));
//
//   // 2. Reload the document browser with the new vault's contents.
//   if (mounted) {
//     DocBrowserWidget.loadVault(context, vault.path);
//   }
//
//   // 3. Optionally refresh the sidebar tree.
//   //    (This will depend on how your AppFlowy sidebar fetches its items.)
//   // _refreshSidebarItems();
// }
//
// // /// Builds the "All Docs" entry that opens the doc browser in a tab.
// Widget _buildAllDocsEntry(BuildContext context) {
//   return ListTile(
//     leading: const Icon(Icons.folder_open_rounded),
//     title: const Text('All Docs'),
//     trailing: const Icon(Icons.chevron_right_rounded, size: 18),
//     dense: true,
//     onTap: () => _openAllDocsTab(context),
//   );
// }
//
// /// Opens [DocBrowserWidget] as a new AppFlowy tab.
// void _openAllDocsTab(BuildContext context) {
//   // AppFlowy's tab API -- adjust to match the actual TabInfo class.
//   // final tabInfo = TabInfo(
//   //   label: 'All Docs',
//   //   icon: Icons.folder_open_rounded,
//   //   pluginId: 'vault_browser',
//   //   widget: BlocProvider.value(
//   //     value: _docBrowserBloc,
//   //     child: DocBrowserWidget(
//   //       onDocOpened: (doc) => _openDocInTab(context, doc),
//   //     ),
//   //   ),
//   // );
//   // context.read<TabsBloc>().add(TabsEvent.openTab(tabInfo));
// }
//
// /// Opens a specific document in a new tab.
// void _openDocInTab(BuildContext context, DocItem doc) {
//   // Fire an event to open the document in a new tab.
//   // This would typically use TabsEvent.openTab with a document viewer.
//   // context.read<TabsBloc>().add(TabsEvent.openTab(TabInfo(
//   //   label: doc.title,
//   //   icon: Icons.article_rounded,
//   //   docPath: doc.path,
//   // )));
// }