"""Bind public document sessions to native preferences while preserving developer profiles.

The storage lease covers MCP selection and retrieval. Detached jobs retain their roots;
nonterminal job records prevent migration after a connection exits. Settings tools run
separately, so the native window can repair preferences when document startup refuses them.
"""

from runtime.app_settings import read_preferences
from runtime.destination_settings import read_destination
from runtime.storage_settings import storage_session


def launch(args, bundle, metadata):
    with storage_session(args.client) as root:
        args.runtime_data_root = root
        if not args.explicit_delivery:
            args.document_response_bytes = read_preferences(args.client).document_response_bytes
        destination = read_destination(args.client)
        if destination.mode == "server":
            from runtime.server_profile import launch as server_launch

            return server_launch(args, metadata, destination)
        from runtime.docling_profile import launch as local_launch
        from runtime.native_selection import SnapshotSelectionProvider, adapter_extensions
        from runtime.selection import SelectionStore

        store = SelectionStore(args.client, extensions=adapter_extensions(), data_root=root)
        args.input_root = store.prepare()
        args.ocr = "true"
        return local_launch(args, bundle, selection_provider=SnapshotSelectionProvider(store))
