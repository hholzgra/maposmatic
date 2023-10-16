{% load i18n %}
{% load l10n %}
{% load extratags %}

function wizardmap(elt, bounds=false) {
   /**
   * Update the 4 text fields with the area coordinates.
   *
   * If a feature has been drawned (bbox != null), the bounding box of the
   * feature is used, otherwise the map extent is used.
   */
  var update_fields = function() {
    if (lock) {
      return;
    }

    clearPaperSize('single');

    var bounds = (bbox != null) ? bbox : map.getBounds();

    $('#id_lat_upper_left').val(bounds.getNorth().toFixed(4));
    $('#id_lon_upper_left').val(lonAdjust(bounds.getWest()).toFixed(4));
    $('#id_lat_bottom_right').val(bounds.getSouth().toFixed(4));
    $('#id_lon_bottom_right').val(lonAdjust(bounds.getEast()).toFixed(4));

    var center = bounds.getCenter();

    var upper_left   = bounds.getNorthWest();
    var upper_right  = bounds.getNorthEast();
    var bottom_left  = bounds.getSouthWest();
    var bottom_right = bounds.getSouthEast();

    var width  = upper_left.distanceTo(upper_right);
    var height = upper_right.distanceTo(bottom_right);

    var rounded_width = Math.round(width);
    var rounded_height = Math.round(height);
    var unit = "m²";

    if (rounded_width > 1000 && rounded_height > 1000) {
      rounded_width = Math.round(width / 1000);
      rounded_height = Math.round(height / 1000);
      unit = " km²";
    }
    $('#lat_upper_left_info').text(   dd2dms(bounds.getNorth(), 'N', 'S') );
    $('#lon_upper_left_info').text(   dd2dms(bounds.getWest(),  'E', 'W') );
    $('#lat_bottom_right_info').text( dd2dms(bounds.getSouth(), 'N', 'S') );
    $('#lon_bottom_right_info').text( dd2dms(bounds.getEast(),  'E', 'W') );
    $('#metric_info').text(
	'( ca. ' + rounded_width + ' x ' + rounded_height + unit + ')'
    );

    var osmid = $('#id_administrative_osmid').val();
    if (osmid) {
      $('#area-size-alert').hide();
      $('#nextlink').show();
    } else if (width < {{ BBOX_MAXIMUM_LENGTH_IN_METERS }} &&
               height < {{ BBOX_MAXIMUM_LENGTH_IN_METERS }}) {
      $('#area-size-alert').hide();
      $('#nextlink').show();

      // Attempt to get the country by reverse geo lookup
	if (countryquery != null) {
	    countryquery.abort();
	}

	countryquery = $.getJSON(
        '/apis/reversegeo/' + center.lat + '/' + center.lng + '/',
        function(data) {
          $.each(data, function(i, item) {
            if (typeof item.country_code != 'undefined') {
              country = item.country_code;
            }
          });
        });
    } else {
      $('#area-size-alert').show();
      $('#nextlink').hide();
    }
  };

  /**
   * Set the map bounds and extent to the current values given by the 4 text
   * fields.
   */
  var set_map_bounds_from_fields = function() {
    lock = true;
    set_map_bounds(map, [
      [$('#id_lat_upper_left').val(), $('#id_lon_upper_left').val()],
      [$('#id_lat_bottom_right').val(), $('#id_lon_bottom_right').val()]
    ]);
    lock = false;
  };


  var map = create_map($('#step-location-map'));
  var lock = false;
  var bbox = null;
  var bbox_style = {
    fill: true,
    fillColor: "#FFFFFF",
    fillOpacity: 0.5,
    stroke: true,
    strokeOpacity: 0.8,
    strokeColor: "#FF0000",
    strokeWidth: 2
  };
  var countryquery = null;
  var filterParams = {
      enableButton: {
          enableText:  '{% trans "Select area" %}',
          disableText: '{% trans "Remove selection" %}'
      },
      adjustButton: {
          text: '{% trans "Select area within current zoom" %}'
      },
      buttonPosition: 'topright'
  };
  if (bounds) {
      filterParams["bounds"] = bounds;
      filterParams["enable"] = true;
      map.fitBounds(bounds);
  }

  locationFilter = new L.LocationFilter(filterParams);
  locationFilter.on("change", function (e) {
      bbox = e.target.getBounds();
      map.fitBounds(bbox);
      update_fields();
  });
  locationFilter.on("enabled", function (e) {
      bbox = e.target.getBounds();
      map.fitBounds(bbox);
      update_fields();
  });
  locationFilter.on("disabled", function (e) {
      bbox = null;
      update_fields();
  });
  locationFilter.addTo(map);

  // locate client position
  L.control.locate().addTo(map);

  // search button
  map.addControl( new L.Control.Search({
      url: '//nominatim.openstreetmap.org/search?format=json&q={s}',
      jsonpParam: 'json_callback',
      propertyName: 'display_name',
      propertyLoc: ['lat','lon'],
      circleLocation: true,
      markerLocation: false,
      autoType: false,
      autoCollapse: true,
      minLength: 2,
      zoom: 14
  }) );

  // Bind events.
  map.on('moveend', update_fields);
  map.on('zoomend', update_fields);

  $('#step-location-bbox input').bind('keydown', function(e) {
    if (bbox) {
      return;
    }

    if (e.keyCode == 38 || e.keyCode == 40) {
      var v = parseFloat($(e.target).val()) + (0.01 * (e.keyCode == 38 ? 1 : -1));
      $(e.target).val(v.toFixed(4));
    }

    set_map_bounds_from_fields();
    update_fields();
  });

  update_fields();
  return map;
}
