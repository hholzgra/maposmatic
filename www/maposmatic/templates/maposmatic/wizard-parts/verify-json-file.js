{% load i18n %}
{% load extratags %}

function verify_json_data(data_str, filename, filenum)
{
    var json_data;

    try {
	json_data = JSON.parse(data_str);
    } catch(e) {
	alert(filename + 'does not look like a valid GeoJson or Umap export file (json parse error)');
	return false;
    }

    if (json_data.type == 'umap') {
	return verify_umap_json_data(json_data, filename, filenum);
    } else if (json_data.type == 'FeatureCollection') {
	return verify_geojson_data(json_data, filename, filenum);
    }

    alert(filename + ' does not look like a valid GeoJson or Umap export file (wrong or missing type info)');

    return false;
}

function verify_geojson_data(json_data, filename, filenum)
{
    var color = file_colors[filenum % file_colors.length];
    var json_layer = L.geoJson(json_data, {
	style: function(feature) {
	    return { color: color };
	}});

    var new_bbox = json_layer.getBounds();

    if ('_northEast' in new_bbox === false) {
	alert(filename + ' does not seem to contain geometry data');
	return false;
    }

    return json_layer;
}

// TODO - this shouldn't be hardcoded, but read from the config file instead
var umap_style_mapping = {
    "OpenStreetMap"            : "CartoOsm",
    "OSM-monochrome"           : "CartoOsmBw",
    "OSM Humanitarian (OSM-FR)": "Humanitarian",
    "OSM-Fr"                   : "French",
    "OSM hikebikemap"          : "HikeBikeMap",
    "OSM Deutschland (OSM-DE)" : "GermanCartoOSM",
    "OSM OpenTopoMap"          : "OpenTopoMap",
    "OSM OpenRiverboatMap"     : "OpenRiverboatMap",
    "OSM Toner (Stamen)"       : "Toner"
};

function verify_umap_json_data(json_data, filename, filenum)
{
    var layer, feature, new_features = [];

    for (layer in json_data.layers) {
	for (feature in json_data.layers[layer].features) {
	    new_features.push(json_data.layers[layer].features[feature]);
	}
    }

    var new_geojson = {'type': 'FeatureCollection', 'features': new_features};

    var color = file_colors[filenum % file_colors.length];
    var json_layer = L.geoJson(new_geojson, {
	style: function(feature) {
	    return { color: color };
	}});
    var new_bbox = json_layer.getBounds();

    if ('_northEast' in new_bbox === false) {
	alert(filename + ' does not seem to contain geometry data');
	return false;
    }

    json_layer.maptitle = json_data.properties.name;

    try {
	var umap_style = json_data.properties.tilelayer.name;
	if (umap_style in umap_style_mapping) {
	    // TODO: add a proper function for selecting the map style
	    $("input:radio[name=stylesheet][value='" + umap_style_mapping[umap_style] + "']").prop("checked", true);
	}
    } catch {
	// ignore 
    }

    return json_layer;
}
