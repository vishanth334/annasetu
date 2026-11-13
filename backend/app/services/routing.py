from app.services.logic import haversine_km, nearest_neighbor


def optimize_route(
    stops: list[dict], start: tuple[float, float] | None = None
) -> tuple[list[dict], float, str]:
    """Use OR-Tools when present; keep the installation-free fallback for local demos."""
    if not stops:
        return [], 0.0, "nearest-neighbour haversine fallback"
    if start is None:
        start = (stops[0]["latitude"], stops[0]["longitude"])
    try:
        from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    except ImportError:
        ordered, distance = nearest_neighbor(stops, start)
        return ordered, distance, "nearest-neighbour haversine fallback"

    locations = [{"latitude": start[0], "longitude": start[1]}, *stops]
    matrix = [
        [
            round(haversine_km(a["latitude"], a["longitude"], b["latitude"], b["longitude"]) * 1000)
            for b in locations
        ]
        for a in locations
    ]
    manager = pywrapcp.RoutingIndexManager(len(locations), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index: int, to_index: int) -> int:
        source = manager.IndexToNode(from_index)
        destination = manager.IndexToNode(to_index)
        return matrix[source][destination]

    callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(callback_index)
    parameters = pywrapcp.DefaultRoutingSearchParameters()
    parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    solution = routing.SolveWithParameters(parameters)
    if solution is None:
        ordered, distance = nearest_neighbor(stops, start)
        return ordered, distance, "nearest-neighbour haversine fallback"

    ordered = []
    index = routing.Start(0)
    total_meters = 0
    while not routing.IsEnd(index):
        next_index = solution.Value(routing.NextVar(index))
        total_meters += routing.GetArcCostForVehicle(index, next_index, 0)
        node = manager.IndexToNode(next_index)
        if node:
            ordered.append(stops[node - 1])
        index = next_index
    return ordered, round(total_meters / 1000, 2), "Google OR-Tools"
