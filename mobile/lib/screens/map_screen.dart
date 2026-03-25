import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});
  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  GoogleMapController? _mapController;

  // Mumbai default center
  static const _initialCamera = CameraPosition(
    target: LatLng(19.0760, 72.8777),
    zoom: 13,
  );

  // Demo risk circles (replace with API heatmap data)
  Set<Circle> get _riskCircles => {
    Circle(
      circleId: const CircleId('danger_1'),
      center:   const LatLng(19.040, 72.855),
      radius:   600,
      fillColor: const Color(0xFFE24B4A).withOpacity(0.25),
      strokeColor: const Color(0xFFE24B4A),
      strokeWidth: 1,
    ),
    Circle(
      circleId: const CircleId('caution_1'),
      center:   const LatLng(19.072, 72.841),
      radius:   500,
      fillColor: const Color(0xFFFAC775).withOpacity(0.25),
      strokeColor: const Color(0xFFFAC775),
      strokeWidth: 1,
    ),
    Circle(
      circleId: const CircleId('safe_1'),
      center:   const LatLng(18.944, 72.823),
      radius:   700,
      fillColor: const Color(0xFF97C459).withOpacity(0.25),
      strokeColor: const Color(0xFF97C459),
      strokeWidth: 1,
    ),
  };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Safety Map', style: TextStyle(fontWeight: FontWeight.w600)),
        actions: [
          IconButton(icon: const Icon(Icons.layers_outlined), onPressed: () {}),
          IconButton(icon: const Icon(Icons.my_location), onPressed: () {
            _mapController?.animateCamera(CameraUpdate.newCameraPosition(_initialCamera));
          }),
        ],
      ),
      body: Stack(children: [
        GoogleMap(
          initialCameraPosition: _initialCamera,
          onMapCreated: (c) => _mapController = c,
          myLocationEnabled: true,
          myLocationButtonEnabled: false,
          circles: _riskCircles,
          mapType: MapType.normal,
        ),

        // Legend
        Positioned(
          top: 12, right: 12,
          child: Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surface,
              borderRadius: BorderRadius.circular(10),
              boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 8)],
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              _LegendItem(color: const Color(0xFFE24B4A), label: 'High risk'),
              _LegendItem(color: const Color(0xFFFAC775), label: 'Caution'),
              _LegendItem(color: const Color(0xFF97C459), label: 'Safe'),
            ]),
          ),
        ),

        // Search bar at bottom
        Positioned(
          bottom: 20, left: 16, right: 16,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surface,
              borderRadius: BorderRadius.circular(30),
              boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 8)],
            ),
            child: Row(children: [
              const Icon(Icons.search, size: 20, color: Colors.grey),
              const SizedBox(width: 8),
              Text('Search location…', style: TextStyle(color: Colors.grey[500], fontSize: 14)),
            ]),
          ),
        ),
      ]),
    );
  }
}

class _LegendItem extends StatelessWidget {
  final Color  color;
  final String label;
  const _LegendItem({required this.color, required this.label});

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 3),
    child: Row(children: [
      Container(width: 12, height: 12, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
      const SizedBox(width: 6),
      Text(label, style: const TextStyle(fontSize: 12)),
    ]),
  );
}
