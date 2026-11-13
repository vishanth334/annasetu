import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerIconRetina from "leaflet/dist/images/marker-icon-2x.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIconRetina,
  shadowUrl: markerShadow,
});

export default function MapView({ points = [], center = [12.9716, 77.5946], height = 360 }) {
  return (
    <div className="map-frame" style={{ height }}>
      <MapContainer center={center} zoom={12} scrollWheelZoom className="map">
        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        {points.map((point) => (
          <Marker key={point.id || `${point.latitude}-${point.longitude}`} position={[point.latitude, point.longitude]}>
            <Popup><strong>{point.item || point.name}</strong>{point.quantity_kg ? ` · ${point.quantity_kg} kg` : ""}</Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
