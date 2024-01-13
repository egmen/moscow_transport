
def get_closest_route(stop_info, routes=[]):
    """Поиск ближайшего транспорта с фильтрацией"""

    closer_route = None
    closer_time = None
    closer_telemetry = None
    for route in stop_info['routePath']:

        if routes and route['number'] not in routes:
            # skip unnecessary route info
            continue

        for event in route['externalForecast']:
            if closer_time is None or closer_time > event['time']:
                closer_route = route['number']
                closer_time = event['time']
                closer_telemetry = event['byTelemetry']

    if closer_route is None:
        return ()

    return (closer_route, closer_time, closer_telemetry)
