"""Init file for the container runtime code."""
from .crt_drivers import CharliecloudDriver, SingularityDriver


drivers = {
    'Charliecloud': CharliecloudDriver,
    'Singularity': SingularityDriver,
}
