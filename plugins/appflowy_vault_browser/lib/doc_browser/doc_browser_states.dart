/// States for the Document Browser BLoC.
library doc_browser_states;

import 'doc_browser_events.dart';

/// Base class for all document browser states.
abstract class DocBrowserState {
  const DocBrowserState();
}

/// Initial idle state — no vault loaded yet.
class DocBrowserInitial extends DocBrowserState {
  const DocBrowserInitial();
}

/// Scanning the vault directory for documents.
class DocBrowserLoading extends DocBrowserState {
  const DocBrowserLoading();
}

/// Documents have been loaded (possibly filtered by search).
class DocBrowserLoaded extends DocBrowserState {
  final List<DocItem> docs;
  final String searchQuery;

  const DocBrowserLoaded({
    required this.docs,
    this.searchQuery = '',
  });

  /// All docs *before* the current search filter is applied.
  List<DocItem> get filteredDocs {
    if (searchQuery.isEmpty) return docs;
    final q = searchQuery.toLowerCase();
    return docs.where((d) => d.title.toLowerCase().contains(q)).toList();
  }

  @override
  String toString() =>
      'DocBrowserLoaded(docs: ${docs.length}, query: "$searchQuery")';
}

/// A document is being opened.
class DocBrowserOpening extends DocBrowserState {
  final DocItem doc;

  const DocBrowserOpening({required this.doc});

  @override
  String toString() => 'DocBrowserOpening(title: ${doc.title})';
}

/// An error occurred while loading documents.
class DocBrowserError extends DocBrowserState {
  final String message;

  const DocBrowserError({required this.message});

  @override
  String toString() => 'DocBrowserError($message)';
}