"""Zoning / GIS provider. Sandbox: not configured."""


class SandboxProvider:
    def zone_for(self, lat: float, lng: float) -> dict:
        return {'zone': None, 'source': 'not_configured'}


def get_provider():
    return SandboxProvider()
