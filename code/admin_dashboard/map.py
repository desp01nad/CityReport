import json
from string import Template

MAP_SIZE = 250
INITIAL_CENTER = [37.97, 23.73]
INITIAL_ZOOM = 11
SELECTED_ZOOM = 16

_LEAFLET_TEMPLATE = Template("""\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>body{margin:0;padding:0;}#map{height:${map_height}px;width:100%;}</style>
</head>
<body>
<div id="map"></div>
<script>
  var map = L.map('map').setView($start_center, $start_zoom);
  L.tileLayer('https://tiles.stadiamaps.com/tiles/osm_bright/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> &copy; OpenMapTiles &copy; OpenStreetMap contributors',
    maxZoom: 20
  }).addTo(map);
  function makeIcon(color) {
    return L.divIcon({
      className: '',
      html: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="36" viewBox="0 0 24 36">' +
            '<path fill="' + color + '" stroke="#fff" stroke-width="1.5" ' +
            'd="M12 0C7.6 0 4 3.6 4 8c0 5.4 8 16 8 16S20 13.4 20 8c0-4.4-3.6-8-8-8z"/>' +
            '<circle fill="#fff" cx="12" cy="8" r="3"/></svg>',
      iconSize: [24, 36],
      iconAnchor: [12, 36],
      tooltipAnchor: [12, -18]
    });
  }
  var redIcon   = makeIcon('#e74c3c');
  var greenIcon = makeIcon('#27ae60');
  var reports    = $reports;
  var selectedId = $selected_id;
  reports.forEach(function(r) {
    L.marker([r.latitude, r.longitude], {
      icon: r.ticket_id === selectedId ? greenIcon : redIcon
    }).bindTooltip('#' + r.ticket_id + ': ' + r.title).addTo(map);
  });
  map.flyTo($target_center, $target_zoom, { animate: true, duration: 0.8 });
</script>
</body>
</html>""")


def build_js_map_html(reports, selected_id, start, target, height=MAP_SIZE):
    markers = [
        {key: r[key] for key in ("ticket_id", "title", "latitude", "longitude")}
        for r in reports
    ]
    return _LEAFLET_TEMPLATE.substitute(
        map_height=height,
        start_center=json.dumps(start["center"]),
        start_zoom=json.dumps(start["zoom"]),
        target_center=json.dumps(target["center"]),
        target_zoom=json.dumps(target["zoom"]),
        reports=json.dumps(markers),
        selected_id=json.dumps(selected_id),
    )
