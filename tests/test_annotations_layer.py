import pytest
from modules.models import MapConfig, CityData, LayerToggles
from modules.map_layers import create_map
import pandas as pd

def test_annotations_layer_rendering():
    """
    Test that the Annotations layer is correctly formed and contains data.
    """
    # Create mock data
    mock_data = CityData(
        df_thermal=pd.DataFrame(),
        df_thermal_points=pd.DataFrame(),
        df_trees=pd.DataFrame(),
        df_water=pd.DataFrame(),
        df_parks=pd.DataFrame(),
        df_shelters=pd.DataFrame(),
        df_fountains=pd.DataFrame(),
        df_green_roofs=pd.DataFrame(),
        df_gardens=pd.DataFrame(),
        df_forests=pd.DataFrame(),
        df_wetlands=pd.DataFrame(),
        df_sensors=pd.DataFrame(),
        df_buildings=pd.DataFrame(),
        df_traffic=pd.DataFrame(),
        current_temp=30.0,
        current_aqi=50
    )
    
    annotations = [
        {"lat": 40.71, "lon": -74.01, "radius": 150, "color": [239, 68, 68, 200], "tooltip": "Test 1"},
        {"lat": 40.72, "lon": -74.02, "radius": 150, "color": [239, 68, 68, 200], "tooltip": "Test 2"}
    ]
    
    config = MapConfig(
        data=mock_data,
        toggles=LayerToggles(trees=True), # Just one toggle
        center_lat=40.7128,
        center_lon=-74.0060,
        simulations=[],
        annotations=annotations
    )
    
    deck = create_map(config)
    
    # Check if the Annotations layer exists
    layers = deck.layers
    annotation_layer = next((l for l in layers if l.id == "Annotations"), None)
    
    assert annotation_layer is not None
    assert len(annotation_layer.data) == 2
    
    # Check if get_position matches our standardization (string-based)
    assert annotation_layer.get_position == "@@=[lon, lat]"
    
    # Verify it works with a list of dicts by check if it can RENDER to json
    try:
        json_res = deck.to_json()
        import json
        parsed = json.loads(json_res)
        layers_json = parsed["layers"]
        ann_json = next((l for l in layers_json if l["id"] == "Annotations"), None)
        assert ann_json is not None
        # Pydeck uses @@type in its serialized JSON
        assert ann_json["@@type"] == "ScatterplotLayer"
        assert ann_json["getPosition"] == "@@=[lon, lat]"
    except Exception as e:
        pytest.fail(f"Pydeck failed to serialize Annotations layer: {e}")
