{% comment %}
 coding: utf-8

 maposmatic, the web front-end of the MapOSMatic city map generation system
 Copyright (C) 2012  David Decotigny
 Copyright (C) 2012  Frédéric Lehobey
 Copyright (C) 2012  Pierre Mauduit
 Copyright (C) 2012  David Mentré
 Copyright (C) 2012  Maxime Petazzoni
 Copyright (C) 2012  Thomas Petazzoni
 Copyright (C) 2012  Gaël Utard
 Copyright (C) 2018  Hartmut Holzgraefe

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as
 published by the Free Software Foundation, either version 3 of the
 License, or any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
{% endcomment %}
{% load i18n %}
{% load extratags %}

{% include "./wizard-parts/little-helpers.js" %}


/**
 * Map creation wizard.
 */

var BBOX_MAXIMUM_LENGTH_IN_KM = {{ BBOX_MAXIMUM_LENGTH_IN_METERS }} / 1000;

var locationFilter = null;
var map = wizardmap($('#step-location-map'){% if SELECTION_BOUNDS %}, {{ SELECTION_BOUNDS }}{% endif  %});
var country = null;
var languages = $('#id_map_language').html();

jQuery.fn.reverse = [].reverse;


$('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
  switch(e.target.id) {
  case 'step-location-admin-tab':
    // If we're switching to the administrative boundary / city search tab, reset
    // the focus inside the input field.
    $('#id_administrative_city').focus();
    break;
  case 'step-location-bbox-tab':
    // trigger map location update via "moveend" event by fake move
    map.panBy([ 1,  1]);
    map.panBy([-1, -1]);
    break;
  }

  setPrevNextLinks();
});

function setPrevNextLinks() {
  var current = $('#step-location-tabs div.item.active');
  var first   = $('#step-location-tabs div.item:first-child');
  var last    = $('#step-location-tabs div.item:last-child');

  $('#prevlink').hide();
  $('#nextlink').hide();
  if (current.attr('id') == first.attr('id')) {
    if ($('#id_administrative_osmid').val()) {
      $('#nextlink').show();
    }
  } else if (current.attr('id') == last.attr('id')) {
    $('#prevlink').show();
  } else {
    $('#prevlink').show();
    $('#nextlink').show();
  }
}

{% include "./wizard-parts/wizardmap.js" %}

{% include "./wizard-parts/upload-files.js" %}

var currentTab = 0; // Current tab is set to be the first tab (0)
showTab(currentTab); // Display the current tab

function showTab(n) {
  // This function will display the specified tab of the form ...
  var x = document.getElementsByClassName("tab");
  x[n].style.display = "block";

  tabName = x[currentTab].id;

  // ... and fix the Previous/Next/Submit buttons:

  if (n == 0) {
    $("#prevlink").hide();
  } else {
    $("#prevlink").show();
  }

  if (tabName == 'wizard-step-lang-title') {
    $("#nextlink").hide();
  } else if (tabName == 'wizard-step-paper-size') {
    // $("#nextlink").hide();
  } else if (tabName == 'wizard-step-location') {
    if ($("#area-size-alert").is(":visible")) {
      $("#nextlink").hide();
    } else {
      $("#nextlink").show();
    }
  } else {
    $("#nextlink").show();
  }

  if (tabName == 'wizard-step-lang-title') {
    $("#formsubmit").show();
  } else {
    $("#formsubmit").hide();
  }

  x = document.getElementsByClassName("btn-circle");
  var i;

  for (i = 0; i < x.length; i++) {
    if (i == n) {
      x[i].classList.add("active");
    } else {
      x[i].classList.remove("active");
    }
  }
}

function nextPrev(n) {
  // This function will figure out which tab to display
  var x = document.getElementsByClassName("tab");

  // Exit the function if any field in the current tab is invalid:
  if (n == 1 && !validateForm()) return false;

  // Hide the current tab:
  x[currentTab].style.display = "none";

  // Increase or decrease the current tab by 1:
  currentTab = currentTab + n;

  tabName = x[currentTab].id;

  switch(tabName) {
    case 'wizard-step-paper-size':
      preparePaperSize();
      break;
    case 'wizard-step-lang-title':
      prepareLangTitle();
      break;
  }

  // if you have reached the end of the form... :
  if (currentTab >= x.length) {
    //...the form gets submitted:
    document.getElementById("regForm").submit();
    return false;
  }
  // Otherwise, display the correct tab:
  showTab(currentTab);
}

function validateForm() {
    // TODO incomplete
    // TODO do we need this at all, given that the submit button only shows when input is complete?
    return true;
}

function country_lang(country_code)
{
    var list    = $('#maplang_choices');
    var success = 0;

    list.find('a').each(function() {
	var langcode = $(this)[0].dataset.langcode;
	if (langcode.substring(3,5) == country_code.toUpperCase()) {
	    $('#map_language_button').html($(this).html());
	    $('#{{ form.map_language.name }}').val($(this)[0].dataset.langcode);
	    success = 1;
	    return false;
	}
    });

    if (!success) {
	list.find('a').each(function() {
	    var langcode = $(this)[0].dataset.langcode;
	    if (langcode == "C") {
		$('#map_language_button').html($(this).html());
		$('#{{ form.map_language.name }}').val('C');
		return false;
	    }
	});
    }
}

{% include "./wizard-parts/prepare-paper-size.js" %}

function prepareLangTitle() {
  // Prepare the language list
    country_lang(country);

  // Set title text
  if ('' == $('#id_maptitle').val()) {
      $('#id_maptitle').val(get_layer_titles());
  }

  // Seed the summary fields
  if ($('#id_administrative_osmid').val()) {
    $('#summary-location').text($('#id_administrative_city').val());
  } else {
      var tl = L.latLng($('#id_lat_upper_left').val(), $('#id_lon_upper_left').val());
      var br = L.latLng($('#id_lat_bottom_right').val(), $('#id_lon_bottom_right').val())
      var bounds = L.latLngBounds(tl,br);

      var width  = Math.round(bounds.getNorthWest().distanceTo(bounds.getNorthEast()) / 1000)
      var height = Math.round(bounds.getNorthWest().distanceTo(bounds.getSouthWest()) / 1000)
    $('#summary-location').html(
	dd2dms($('#id_lat_upper_left').val(), 'N', 'S') + ', ' +
        dd2dms($('#id_lon_upper_left').val(), 'E', 'W') +
	'&nbsp;&#8600;&nbsp;' +
        dd2dms($('#id_lat_bottom_right').val(), 'N', 'S') + ', ' +
        dd2dms($('#id_lon_bottom_right').val(), 'E', 'W') +
	'&nbsp;&nbsp; ( ca. '+ width + ' x ' + height + ' km² )'
    );
  }

  $('#summary-layout').text($('input[name=layout]:checked').parent().text());
  $('#summary-stylesheet').text($('select[name=stylesheet] option:selected').text());

  var overlay_str = "";
  $( "select[name=overlay] option:selected" ).each(function() {
    overlay_str += $( this ).text() + ", ";
  });

  $('#summary-overlay').text(overlay_str.slice(0,-2));


  var paper_text = "";
  paper_text = paper_text + $('#id_paper_width_mm').val();
  paper_text = paper_text + ' x ' + $('#id_paper_height_mm').val() + ' mm²';
  // TODO re-add paper size name and orientation where applicable  

  $('input[value=portrait]').prop("disabled", false);
  $('input[value=landscape]').prop("disabled", false);

  $('#summary-paper-size').text(paper_text);
}
