from app.services.logic import haversine_km, nearest_neighbor


def test_haversine_distance_is_symmetric_and_reasonable():
    north = haversine_km(12.9716, 77.5946, 13.0827, 80.2707)
    south = haversine_km(13.0827, 80.2707, 12.9716, 77.5946)
    assert 280 < north < 300
    assert abs(north - south) < 0.001


def test_nearest_neighbor_orders_nearby_pickup_first():
    stops = [
        {"id": 2, "latitude": 12.99, "longitude": 77.60},
        {"id": 1, "latitude": 12.972, "longitude": 77.595},
    ]
    ordered, distance = nearest_neighbor(stops, (12.9716, 77.5946))
    assert [stop["id"] for stop in ordered] == [1, 2]
    assert distance > 0
