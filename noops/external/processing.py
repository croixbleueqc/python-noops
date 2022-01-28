"""
Provide an abstraction code to implement a Service Catalog Processing script
to convert a service request (noops.yaml) to "native objects"
"""

from typing import List
from pathlib import Path
import yaml
import click

class Processing:
    """
    Processing Abstract Class
    """
    def convert(self, service_request: dict, name: str) -> List[dict]:
        """Convert a service requests to an object list

        Kubernetes:
        - Do NOT set metadata as the field will be overriden

        Return example:
        [
            {
                "apiVersion": "unittest.local/v1",
                "kind": "Test",
                "spec": {
                    "key": service_request.get("key")
                }
            }
        ]
        """
        raise NotImplementedError()

    def _store(self, objs: dict, output: Path, indent=2):
        """Store Objects to the requested file"""
        with output.open(mode='w', encoding='UTF-8') as file:
            yaml.dump(objs, stream=file, indent=indent)

    def _load(self, request: Path) -> dict:
        """Load service request"""
        return yaml.safe_load(
            Path(request).read_text(encoding='UTF-8')
        )

    def run(self):
        """Start the command line"""

        @click.group(
            context_settings=dict(help_option_names=["-h", "--help"]),
            invoke_without_command=True
        )
        @click.option('-n', '--name', help='metadata.name used', required=True)
        @click.option('-r', '--request',
            help='service request (yaml)', type=click.Path(exists=True), required=True)
        @click.option('-o', '--objects',
            help='service catalog objects (yaml)', type=click.Path(), required=True)
        def cli(name, request, objects):
            """Create objects based on plan/class'"""

            service_request = self._load(Path(request))

            objs = self.convert(service_request, name)
            self._store(objs, Path(objects))

        cli() # pylint: disable=no-value-for-parameter
