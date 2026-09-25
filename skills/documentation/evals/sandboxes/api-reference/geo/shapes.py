from dataclasses import dataclass


@dataclass
class Box:
    """A latitude and longitude bounding box.

    Parameters
    ----------
    south, west, north, east : float
        Edges, in degrees.
    """

    south: float
    west: float
    north: float
    east: float

    def contains(self, lat: float, lon: float) -> bool:
        """Whether a point lies inside the box, edges included.

        Raises
        ------
        ValueError
            If the box crosses the antimeridian (west > east).
        """
        if self.west > self.east:
            raise ValueError("boxes across the antimeridian are not supported")
        return self.south <= lat <= self.north and self.west <= lon <= self.east
