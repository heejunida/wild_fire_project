// js/map-utils.js

export function initializeMap(containerId, centerLatLng, level = 9) {
  const container = document.getElementById(containerId);
  const options = {
    center: centerLatLng,
    level: level
  };
  return new kakao.maps.Map(container, options);
}

export function setMapCenter(map, latLng) {
  map.setCenter(latLng);
}

export function addMarker(map, position) {
  return new kakao.maps.Marker({
    map: map,
    position: position
  });
}