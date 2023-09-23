{% load i18n %}
{% load extratags %}

{% include "./verify-gpx-file.js" %}
{% include "./verify-json-file.js" %}

var file_colors = ['red', 'blue', 'green', 'violet', 'orange'];

var upload_file_layers = [];
var upload_file_bounds = false;

function clear_upload_layers() {
    var old_layer;
    for (old_layer of upload_file_layers) {
	old_layer.removeFrom(map);
    }
    upload_file_layers = [];
    upload_file_bounds = false;
    $("#file-list").text('');
}

function add_upload_layer(filename, new_layer) {
    new_layer.addTo(map);
    // txt += delim + files[i].name;
    // delim = '; ';

    upload_file_layers.push(new_layer);

    var new_bbox = new_layer.getBounds();

    if (upload_file_bounds == false) {
	upload_file_bounds = new_bbox;
    } else {
	upload_file_bounds.extend(new_bbox);
    }

    map.fitBounds(upload_file_bounds);

    if (upload_file_bounds.getSouthWest().equals(upload_file_bounds.getNorthEast())) {
	upload_file_bounds = map.getBounds();
    }

    upload_file_bounds = upload_file_bounds.pad(0.1);
    map.fitBounds(upload_file_bounds);

    // TODO: fill file list display
    // $("#file-list").text(txt);

    // we need to have the map visible to correctly apply the new bounds, apparently
    // so we are quickly switching between tabs back and forth
    $('#step-location-bbox-tab').tab('show');
    locationFilter.setBounds(upload_file_bounds);
    locationFilter.enable();
    $('#step-location-file-tab').tab('show');

    // enable "to preview" button
    $('#upload_preview_button').show();
}

function get_layer_titles() {
    var layer, titles = [];

    for (layer of upload_file_layers) {
	if (layer.hasOwnProperty('maptitle')) {
	    titles.push(layer.maptitle);
	}
    }

    return titles.join("; ");
}

$("#id_uploadfile").change(function() {
    var upload_file;

    clear_upload_layers();

    var n = 0;
    for (upload_file of $("#id_uploadfile")[0].files) {
	var fr, file;

	file = upload_file;
	fr = new FileReader();
	fr.filename = file.name;
	fr.filenum = n;
	n = n + 1;
	fr.onload = function (e) {
	    if (e.target.result) {
		layer = verify_upload_file(file.name, e.target.result, e.target.filenum);
		if (layer != false) {
		    add_upload_layer(e.target.filename, layer);
		}
	    } else {
		alert("Could not read " + e.target.filename);
	    }
	};
	fr.readAsText(upload_file);
    }


});

function verify_upload_file(filename, data_str, filenum) {
    if (data_str.startsWith('<?xml')) {
	return verify_gpx_data(data_str, filename, filenum);
    } else if (data_str.startsWith('{')) {
	return verify_json_data(data_str, filename, filenum);
    }

    alert(filename + ": unknown file type");
    return false;
}
