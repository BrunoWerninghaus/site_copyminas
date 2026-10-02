from urllib.parse import quote_plus


COPY_MINAS_LOCATION = {
    "name": "Copy Minas",
    "city": "Elói Mendes",
    "state": "MG",
    "address": "Rua Tonico da Serra, 89 - Ludovico Pavoni, Elói Mendes - MG, 37110-000",
    # Globe-scale marker: municipal seat / urban center of Elói Mendes.
    # The Google Maps action below uses the exact business address.
    "latitude": -21.6094,
    "longitude": -45.5660,
}

_maps_query = quote_plus(
    f"{COPY_MINAS_LOCATION['name']}, {COPY_MINAS_LOCATION['address']}"
)

COPY_MINAS_LOCATION["maps_url"] = (
    "https://www.google.com/maps/search/?api=1&query="
    f"{_maps_query}"
)
