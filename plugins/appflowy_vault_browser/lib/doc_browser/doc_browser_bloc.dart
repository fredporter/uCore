/// BLoC for browsing all documents in the active vault.
///
/// Walks the vault directory tree, discovers markdown (`.md`) and
/// `.afdoc` documents, and provides search/filter capabilities.
library doc_browser_bloc;

import 'dart:async';
import 'dart:io';

import 'package:flutter_bloc/flutter_bloc.dart';

import 'doc_browser_events.dart';
import 'doc_browser_states.dart';

/// Scans a vault directory for documents and manages the doc list state.
///
/// The bloc listens for [LoadDocsEvent] (triggered by vault switch or
/// manual refresh) and [SearchDocsEvent] for client-side filtering.
class DocBrowserBloc extends Bloc<DocBrowserEvent, DocBrowserState> {
  /// The currently known set of docs, used as the baseline for filtering.
  List<DocItem> _allDocs = [];

  /// Current active vault path.
  String? _activeVaultPath;

  DocBrowserBloc() : super(const DocBrowserInitial()) {
    on<LoadDocsEvent>(_onLoadDocs);
    on<SearchDocsEvent>(_onSearchDocs);
    on<OpenDocEvent>(_onOpenDoc);
  }

  /// Resolves the user's home directory, accounting for environment variables.
  static String get _homeDir {
    final envHome = Platform.environment['HOME'];
    if (envHome != null && envHome.isNotEmpty) return envHome;
    if (Platform.isMacOS || Platform.isLinux) {
      return '/Users/${Platform.environment['USER'] ?? 'user'}';
    }
    return Platform.environment['USERPROFILE'] ??
        'C:\\Users\\${Platform.environment['USERNAME'] ?? 'user'}';
  }

  /// Expand a vault path (may contain '~') to an absolute [Directory].
  Directory _resolveVaultPath(String vaultPath) {
    final expanded = vaultPath.startsWith('~/')
        ? '${_homeDir}${vaultPath.substring(1)}'
        : vaultPath;
    return Directory(expanded);
  }

  Future<void> _onLoadDocs(
    LoadDocsEvent event,
    Emitter<DocBrowserState> emit,
  ) async {
    _activeVaultPath = event.vaultPath;
    emit(const DocBrowserLoading());

    try {
      final dir = _resolveVaultPath(event.vaultPath);
      if (!await dir.exists()) {
        emit(const DocBrowserError(
          message: 'Vault directory not found.',
        ));
        return;
      }

      _allDocs = await _scanDirectory(dir);
      emit(DocBrowserLoaded(docs: _allDocs));
    } on FileSystemException catch (e) {
      emit(DocBrowserError(message: 'Filesystem error: ${e.message}'));
    } catch (e) {
      emit(DocBrowserError(message: 'Failed to scan vault: $e'));
    }
  }

  void _onSearchDocs(
    SearchDocsEvent event,
    Emitter<DocBrowserState> emit,
  ) {
    final currentState = state;
    if (currentState is DocBrowserLoaded) {
      emit(DocBrowserLoaded(
        docs: currentState.docs,
        searchQuery: event.query,
      ));
    }
  }

  Future<void> _onOpenDoc(
    OpenDocEvent event,
    Emitter<DocBrowserState> emit,
  ) async {
    emit(DocBrowserOpening(doc: event.doc));

    // The actual tab-open logic is handled by the widget callback
    // via the `onDocOpened` stream. After a brief delay, return to
    // the loaded state.
    await Future.delayed(const Duration(milliseconds: 300));

    final currentState = state;
    if (currentState is DocBrowserOpening) {
      emit(DocBrowserLoaded(
        docs: _allDocs,
        searchQuery: '',
      ));
    }
  }

  /// Recursively walk [dir], collecting [DocItem] entries for markdown
  /// and AppFlowy document files.
  Future<List<DocItem>> _scanDirectory(Directory dir) async {
    final items = <DocItem>[];
    final homePrefix = _homeDir;

    await for (final entity in dir.list(recursive: true)) {
      if (entity is File) {
        final fileName = entity.path.split(Platform.pathSeparator).last;
        final relativePath = entity.path.startsWith(homePrefix)
            ? '~${entity.path.substring(homePrefix.length)}'
            : entity.path;

        if (_isDocumentFile(fileName)) {
          items.add(DocItem(
            id: entity.path,
            title: _titleFromFileName(fileName),
            path: relativePath,
            lastModified: await entity.lastModified(),
          ));
        }
      }
    }

    // Sort by last-modified descending (most recent first).
    items.sort((a, b) {
      final ma = a.lastModified ?? DateTime(1970);
      final mb = b.lastModified ?? DateTime(1970);
      return mb.compareTo(ma);
    });

    return items;
  }

  /// Return `true` if [fileName] is a recognised document format.
  bool _isDocumentFile(String fileName) {
    final lower = fileName.toLowerCase();
    return lower.endsWith('.md') ||
        lower.endsWith('.afdoc') ||
        lower.endsWith('.markdown') ||
        lower.endsWith('.txt');
  }

  /// Derive a human-readable title from a file name.
  String _titleFromFileName(String fileName) {
    // Strip known extensions.
    String title = fileName;
    for (final ext in ['.md', '.afdoc', '.markdown', '.txt']) {
      if (fileName.toLowerCase().endsWith(ext)) {
        title = fileName.substring(0, fileName.length - ext.length);
        break;
      }
    }
    // Replace hyphens / underscores with spaces.
    title = title.replaceAll(RegExp(r'[-_]'), ' ');
    // Title-case each word.
    return title
        .split(' ')
        .where((w) => w.isNotEmpty)
        .map((w) => '${w[0].toUpperCase()}${w.substring(1)}')
        .join(' ');
  }
}