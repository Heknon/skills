# billing

Team rule: routes call a service, services call a repository, even when
the service only forwards. Only repositories import Beanie documents'
query API.
