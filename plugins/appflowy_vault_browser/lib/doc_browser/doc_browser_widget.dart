/// Document Browser widget — searchable list of all docs in a vault.
///
/// Intended to be rendered as a full tab/page. Shows a search bar
/// at the top, a count chip, and a scrollable list of [DocItem] cards.
/// Tapping a card fires the [onDocOpened] callback so the host app
/// can open the document via `TabsEvent.openTab` or equivalent.
library doc_browser_widget;

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'doc_browser_bloc.dart';
import 'doc_browser_events.dart';
import 'doc_browser_states.dart';

/// Full-page widget that displays all documents in the active vault.
///
/// Requires a [DocBrowserBloc] in the widget tree (provided by a
/// `BlocProvider`). Call [loadVault] to trigger a scan when the
/// active vault changes.
///
/// Usage:
/// ```dart
/// BlocProvider(
///   create: (_) => DocBrowserBloc(),
///   child: DocBrowserWidget(
///     onDocOpened: (doc) => print('Open: ${doc.title}'),
///   ),
/// )
/// ```
class DocBrowserWidget extends StatefulWidget {
  /// Invoked when the user taps a document. The host app should use
  /// this to open the file in a new tab or navigate to it.
  final void Function(DocItem doc)? onDocOpened;

  const DocBrowserWidget({
    super.key,
    this.onDocOpened,
  });

  @override
  State<DocBrowserWidget> createState() => _DocBrowserWidgetState();

  /// Convenience: tells the BLoC to scan the given vault path.
  /// Call from the host whenever the active vault changes.
  static void loadVault(BuildContext context, String vaultPath) {
    context.read<DocBrowserBloc>().add(LoadDocsEvent(vaultPath: vaultPath));
  }
}

class _DocBrowserWidgetState extends State<DocBrowserWidget> {
  final _searchController = TextEditingController();
  Timer? _debounce;

  @override
  void dispose() {
    _debounce?.cancel();
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<DocBrowserBloc, DocBrowserState>(
      listener: _onStateChanged,
      builder: (context, state) => _buildScaffold(context, state),
    );
  }

  void _onStateChanged(BuildContext context, DocBrowserState state) {
    if (state is DocBrowserOpening) {
      widget.onDocOpened?.call(state.doc);
    }
    if (state is DocBrowserError) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(state.message),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  Widget _buildScaffold(BuildContext context, DocBrowserState state) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _SearchBar(controller: _searchController, onChanged: _onSearchChanged),
        const Divider(height: 1),
        Expanded(child: _buildBody(context, state)),
      ],
    );
  }

  void _onSearchChanged(String query) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 200), () {
      if (!mounted) return;
      context.read<DocBrowserBloc>().add(SearchDocsEvent(query: query));
    });
  }

  Widget _buildBody(BuildContext context, DocBrowserState state) {
    switch (state) {
      case DocBrowserInitial():
        return _buildPlaceholder(context, 'Select a vault to browse documents.');
      case DocBrowserLoading():
        return const Center(child: CircularProgressIndicator());
      case DocBrowserLoaded(:final filteredDocs, :final searchQuery):
        return _buildDocList(context, filteredDocs, searchQuery);
      case DocBrowserOpening(:final doc):
        return _buildDocList(
          context,
          (state is DocBrowserLoaded) ? (state as DocBrowserLoaded).filteredDocs : [],
          '',
        );
      case DocBrowserError(:final message):
        return _buildError(context, message);
      default:
        return const SizedBox.shrink();
    }
  }

  Widget _buildPlaceholder(BuildContext context, String message) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.folder_open_rounded,
              size: 48,
              color: Theme.of(context)
                  .colorScheme
                  .onSurfaceVariant
                  .withValues(alpha: 0.4),
            ),
            const SizedBox(height: 16),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildError(BuildContext context, String message) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.error_outline_rounded,
              size: 48,
              color: Theme.of(context).colorScheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.error,
                  ),
            ),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: () {
                context.read<DocBrowserBloc>().add(const LoadDocsEvent(
                  vaultPath: '',
                ));
              },
              child: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDocList(
    BuildContext context,
    List<DocItem> docs,
    String searchQuery,
  ) {
    if (docs.isEmpty && searchQuery.isNotEmpty) {
      return _buildPlaceholder(
        context,
        'No documents match "$searchQuery".',
      );
    }
    if (docs.isEmpty) {
      return _buildPlaceholder(
        context,
        'This vault contains no documents yet.',
      );
    }

    return Column(
      children: [
        // Count chip row.
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            children: [
              Text(
                '${docs.length} document${docs.length == 1 ? '' : 's'}',
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
              ),
              if (searchQuery.isNotEmpty) ...[
                const SizedBox(width: 8),
                Chip(
                  label: Text(
                    '"$searchQuery"',
                    style: const TextStyle(fontSize: 11),
                  ),
                  deleteIcon: const Icon(Icons.close, size: 14),
                  onDeleted: () {
                    _searchController.clear();
                    context
                        .read<DocBrowserBloc>()
                        .add(const SearchDocsEvent(query: ''));
                  },
                  visualDensity: VisualDensity.compact,
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
              ],
            ],
          ),
        ),
        // Document list.
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            itemCount: docs.length,
            itemBuilder: (context, index) => _DocCard(
              doc: docs[index],
              onTap: () {
                context.read<DocBrowserBloc>().add(OpenDocEvent(doc: docs[index]));
              },
            ),
          ),
        ),
      ],
    );
  }
}

/// Search bar with a clear button.
class _SearchBar extends StatelessWidget {
  final TextEditingController controller;
  final ValueChanged<String> onChanged;

  const _SearchBar({
    required this.controller,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 12, 12, 8),
      child: TextField(
        controller: controller,
        onChanged: onChanged,
        decoration: InputDecoration(
          hintText: 'Search documents…',
          prefixIcon: const Icon(Icons.search_rounded, size: 20),
          suffixIcon: controller.text.isNotEmpty
              ? IconButton(
                  icon: const Icon(Icons.clear_rounded, size: 18),
                  onPressed: () {
                    controller.clear();
                    onChanged('');
                  },
                )
              : null,
          filled: true,
          contentPadding:
              const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: BorderSide.none,
          ),
        ),
      ),
    );
  }
}

/// Tappable card for a single document in the browse list.
class _DocCard extends StatelessWidget {
  final DocItem doc;
  final VoidCallback onTap;

  const _DocCard({required this.doc, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 3),
      elevation: 0,
      color: scheme.surfaceContainerLow,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Row(
            children: [
              // Doc type icon.
              Icon(
                _iconForDoc(doc),
                size: 22,
                color: scheme.primary.withValues(alpha: 0.7),
              ),
              const SizedBox(width: 12),
              // Title + path.
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      doc.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style:
                          Theme.of(context).textTheme.bodyMedium?.copyWith(
                                fontWeight: FontWeight.w600,
                              ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      doc.path,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style:
                          Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: scheme.onSurfaceVariant
                                    .withValues(alpha: 0.6),
                                fontSize: 11,
                              ),
                    ),
                  ],
                ),
              ),
              // Last-modified badge.
              if (doc.lastModified != null)
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(4),
                    color: scheme.surfaceContainerHighest,
                  ),
                  child: Text(
                    _formatRelative(doc.lastModified!),
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: scheme.onSurfaceVariant,
                          fontSize: 10,
                        ),
                  ),
                ),
              const SizedBox(width: 4),
              Icon(
                Icons.chevron_right_rounded,
                size: 18,
                color: scheme.onSurfaceVariant.withValues(alpha: 0.4),
              ),
            ],
          ),
        ),
      ),
    );
  }

  IconData _iconForDoc(DocItem doc) {
    final lower = doc.path.toLowerCase();
    if (lower.endsWith('.md') || lower.endsWith('.markdown')) {
      return Icons.article_rounded;
    }
    if (lower.endsWith('.afdoc')) {
      return Icons.description_rounded;
    }
    return Icons.note_alt_rounded;
  }

  /// Human-readable relative time string (e.g., "3h ago", "2d ago").
  String _formatRelative(DateTime dateTime) {
    final now = DateTime.now();
    final diff = now.difference(dateTime);

    if (diff.inSeconds < 60) return 'now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    if (diff.inDays < 7) return '${diff.inDays}d ago';
    if (diff.inDays < 30) return '${(diff.inDays / 7).floor()}w ago';
    if (diff.inDays < 365) return '${(diff.inDays / 30).floor()}mo ago';
    return '${(diff.inDays / 365).floor()}y ago';
  }
}