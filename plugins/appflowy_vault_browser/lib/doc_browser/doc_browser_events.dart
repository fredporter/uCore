/// Events for the Document Browser BLoC.
library doc_browser_events;

/// A single document preview returned from the vault query.
class DocItem {
  final String id;
  final String title;
  final String path;
  final String? workspaceId;
  final String? appId;
  final DateTime? lastModified;

  const DocItem({
    required this.id,
    required this.title,
    required this.path,
    this.workspaceId,
    this.appId,
    this.lastModified,
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is DocItem && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;

  @override
  String toString() => 'DocItem(id: $id, title: $title)';
}

/// Base class for all document browser events.
abstract class DocBrowserEvent {
  const DocBrowserEvent();
}

/// Load all documents for a given vault path.
class LoadDocsEvent extends DocBrowserEvent {
  final String vaultPath;

  const LoadDocsEvent({required this.vaultPath});

  @override
  String toString() => 'LoadDocsEvent(vaultPath: $vaultPath)';
}

/// User typed into the search/filter bar.
class SearchDocsEvent extends DocBrowserEvent {
  final String query;

  const SearchDocsEvent({required this.query});

  @override
  String toString() => 'SearchDocsEvent(query: $query)';
}

/// User tapped a document to open it.
class OpenDocEvent extends DocBrowserEvent {
  final DocItem doc;

  const OpenDocEvent({required this.doc});

  @override
  String toString() => 'OpenDocEvent(doc: ${doc.title})';
}