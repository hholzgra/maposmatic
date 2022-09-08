{% load i18n %}
{% load extratags %}

var papersize_prepared = false;

function clearPaperSize(layout) {
    papersize_prepared = false;

    choose_paper_buttons(layout);
}


function choose_paper_buttons(layout)
{
    if (layout.startsWith('multi')) {
	$('#single_page_sizes').hide();
	// $('#papersize_formline').hide();
	$('#multi_page_sizes').show();
    } else {
	$('#single_page_sizes').show();
	// $('#papersize_formline').show();
	$('#multi_page_sizes').hide();
    }
}



var best_fit_width  = 0;
var best_fit_height = 0;
var best_fit_scale  = 0;

function preparePaperSize() {
  if (papersize_prepared) {
    $('#nextlink').show();
    return;
  }

  $('#paper-wait').show();
  $('#paper-size').hide();
  $('#paper-size-loading-error').hide();
  $('#paper-size-loading').show();
  $('#nextlink').hide();

  var args = null;
  if ($('#id_administrative_osmid').val()) {
    args = {
      osmid: $('#id_administrative_osmid').val(),
    };
  } else {
    args = {
      lat_upper_left: $('#id_lat_upper_left').val(),
      lon_upper_left: $('#id_lon_upper_left').val(),
      lat_bottom_right: $('#id_lat_bottom_right').val(),
      lon_bottom_right: $('#id_lon_bottom_right').val()
    };
  }

  // make the next two lines work with select boxes, too
  args['layout'] = $('input[name=layout]:checked').val();
  args['indexer'] = $('input[name=indexer]:checked').val();

  args['stylesheet'] = $('input[name=stylesheet]:checked').val();
  if (!args['stylesheet']) {
      args['stylesheet'] = $('#id_stylesheet :selected').val();
  }
  args['overlay'] = $('input[name=overlay]:checked').val();
  if (!args['overlay']) {
      args['overlay'] = $('#id_overlay :selected').val();
  }

  $.ajax('/apis/papersize/', { type: 'post', data: args })
   .fail(function() { $('#paper-size-loading-error').show(); })
   .always(function() { $('#paper-size-loading').hide(); })
   .done(function(data) {
       var i;

       best_fit_width  = 0;
       best_fit_height = 0;
       best_fit_scale  = 0;

       disable_all_papersizes();
       choose_paper_buttons(args['layout']);

       for (i in data) {
	   var w = data[i]['width'];
	   var h = data[i]['height'];

	   if (data[i]['name'] == 'Best fit') {
	       // update min width/height input limits
	       $('#id_paper_width_mm').attr("min", w);
	       $('#id_paper_height_mm').attr("min", h);

	       best_fit_width  = parseInt(w);
	       best_fit_height = parseInt(h);
	       best_fit_scale  = parseInt( data[i][(data[i]['portrait_ok']) ? 'portrait_scale' : 'landscape_scale']);

	       $("#best_width").text(w);
	       $("#best_height").text(h);

	       // if current values are below limits -> enforce min size
	       if (w > parseInt($('#id_paper_width_mm').val())
		   || h > parseInt($('#id_paper_height_mm').val())) {
		   $('#id_paper_width_mm').val(w);
		   $('#id_paper_height_mm').val(h);
	       }

	       w = h = 0;
	   }

	   if (data[i]['portrait_ok']) {
	       var scale = Math.round(parseInt(data[i]['portrait_scale']));
	       var scale_txt = "";
	       if (scale) {
		   scale_txt = "Scale ca. 1:" + scale + "; zoom factor " + data[i]['portrait_zoom'];
	       }
	       enable_papersize(w, h, scale_txt);
	   }
	   if (data[i]['landscape_ok']) {
	       var scale = Math.round(parseInt(data[i]['landscape_scale']));
	       var scale_txt = "";
	       if (scale) {
		   scale_txt = "Scale ca. 1:" + scale + "; zoom factor " + data[i]['landscape_zoom'];
	       }
	       enable_papersize(h,w, scale_txt);
	   }
       }

       set_papersize($('#id_paper_width_mm').val(),$('#id_paper_height_mm').val());

       $('#paper-wait').hide();
       $('#paper-size').show();

       return null;
    });
}

function change_papersize()
{
    w = parseInt($('#id_paper_width_mm').val());
    h = parseInt($('#id_paper_height_mm').val());

    wmin = parseInt($('#id_paper_width_mm').attr('min'));
    hmin = parseInt($('#id_paper_height_mm').attr('min'));

    if (w < wmin) {
	w = wmin;
    }

    if (h < hmin) {
	h = hmin;
    }

    set_papersize(w ,h);
}

function set_papersize(paper_width, paper_height)
{
    // remove existing button mark (if any)
    $('.papersize:enabled').each(function(index) {
	unmark_button($(this));
    });

    // mark button that matches this size (if any)
    var id;

    if (paper_width == 0 && paper_height == 0) {
	id = ".papersize_best_fit";
	paper_width = parseInt($("#best_width").text());
	paper_height = parseInt($("#best_height").text());
    } else if (paper_width == parseInt($("#best_width").text())
	       && paper_height == parseInt($("#best_height").text())) {
	id = ".papersize_best_fit";
    } else {
	id = ".papersize_" + paper_width + "_" + paper_height;
    }

    var buttons = $(id);

    if (buttons.length) {
	mark_button(buttons);
    }

    $("#id_paper_width_mm").val(paper_width);
    $("#id_paper_height_mm").val(paper_height);

    // show preview in HTML canvas
    var scale = 0;
    if (best_fit_scale) {
	scale = Math.floor(best_fit_scale / Math.min(paper_width / best_fit_width, paper_height / best_fit_height));
    }
    show_paper_preview('paper_canvas', paper_width, paper_height, scale);

    // we can now proceed to next step
    $('#nextlink').show();
}

function show_paper_preview(canvas_name, w, h, scale)
{
    var canvas = document.getElementById(canvas_name);
    var ctx = canvas.getContext("2d");
    var cw = canvas.width-1;
    var ch = canvas.height-1;

    w = parseInt(w);
    h = parseInt(h);

    if (w > h) {
	tw = (cw - 20)
	dw = 20;
	th = tw * (h/w);
	dh = (ch-th)/2;
    } else {
	th = (ch - 20)
	dh = 20;
	tw = th * (w/h);
	dw = (cw-tw)/2;
    }

    ctx.save();
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // scale bar style settings
    ctx.strokeStyle = "#00007F";
    ctx.fillStyle = "#00007F";

    //
    // vertical scale
    //
    // top edge
    ctx.beginPath();
    ctx.moveTo(dw - 20, dh);
    ctx.lineTo(dw - 10, dh);
    ctx.stroke();

    // top arrow tip
    ctx.beginPath();
    ctx.moveTo(dw - 15, dh);
    ctx.lineTo(dw - 20, dh+10);
    ctx.lineTo(dw - 10, dh+10);
    ctx.fill();

    // upper half of height bar
    ctx.beginPath();
    ctx.moveTo(dw - 15, dh+10);
    ctx.lineTo(dw - 15, dh+th/2-20);
    ctx.stroke();

    // height text
    ctx.font = '10px serif';
    ctx.textAlign = 'center';
    ctx.save();
    ctx.translate(dw-10, dh+th/2);
    ctx.rotate(-Math.PI/2);
    ctx.fillText(h, 0, 0);
    ctx.restore();

    // lower half of height bar
    ctx.beginPath();
    ctx.moveTo(dw - 15, dh+th-10);
    ctx.lineTo(dw - 15, dh+th/2+20);
    ctx.stroke();

    // bottom arrow tip
    ctx.beginPath();
    ctx.moveTo(dw - 15, dh+th);
    ctx.lineTo(dw - 20, dh+th-10);
    ctx.lineTo(dw - 10, dh+th-10);
    ctx.fill();

    // bottom edge
    ctx.beginPath();
    ctx.moveTo(dw - 20, dh+th);
    ctx.lineTo(dw - 10, dh+th);
    ctx.stroke();

    //
    // horiziontal scale
    //

    // left edge
    ctx.beginPath();
    ctx.moveTo(dw, dh-20);
    ctx.lineTo(dw, dh-10);
    ctx.stroke();

    // left arrow tip
    ctx.beginPath();
    ctx.moveTo(dw, dh - 15);
    ctx.lineTo(dw+10, dh - 20);
    ctx.lineTo(dw+10, dh - 10);
    ctx.fill();

    // left half of width bar
    ctx.beginPath();
    ctx.moveTo(dw+10, dh - 15);
    ctx.lineTo(dw+tw/2-20, dh - 15);
    ctx.stroke();

    // width text
    ctx.font = '10px serif';
    ctx.textAlign = 'center';
    ctx.fillText(w, dw+tw/2, dh - 10);

    // right half of width bar
    ctx.beginPath();
    ctx.moveTo(dw+tw-10, dh - 15);
    ctx.lineTo(dw+tw/2+20, dh - 15);
    ctx.stroke();

    // right arrow tip
    ctx.beginPath();
    ctx.moveTo(dw+tw, dh - 15);
    ctx.lineTo(dw+tw-10, dh - 20);
    ctx.lineTo(dw+tw-10, dh - 10);
    ctx.fill();

    // right edge
    ctx.beginPath();
    ctx.moveTo(dw+tw, dh - 20);
    ctx.lineTo(dw+tw, dh - 10);
    ctx.stroke();

    //
    // inner decoration
    //

    // show actual selected area
    ctx.fillStyle = "#DEDEFF";
    if (scale) { // only set on single page formats
	var canvas_aspect = tw / th;
	var selection_aspect = best_fit_width / best_fit_height;

	var aw = tw;
	var ah = th;
	var oh = 0;
	var ow = 0;

	if (selection_aspect > canvas_aspect) {
	    ah = ah * canvas_aspect / selection_aspect;
	    oh = (th - ah) / 2;
	} else if (selection_aspect < canvas_aspect) {
	    aw = aw * selection_aspect / canvas_aspect;
	    ow = (tw - aw) / 2;
	}

	ctx.fillRect(dw + ow, dh + oh, aw, ah);
    } else {
	ctx.fillRect(dw, dh, tw, th);
    }

    // dashed paper diagonals
    ctx.beginPath();
    ctx.strokeStyle = "#000000";
    ctx.setLineDash([4, 2]);
    ctx.moveTo(dw, dh);
    ctx.lineTo(dw+tw, dh+th);
    ctx.moveTo(dw, dh+th);
    ctx.lineTo(dw+tw, dh);
    ctx.stroke();

    // scale and zoom factors
    if (scale) {
	ctx.font = '10px serif';
	ctx.textAlign = 'center';
	ctx.strokeStyle = "#000000";
	ctx.fillStyle = "#000000";
	ctx.fillText('ca. 1:' + scale, dw+tw/2, dh+th/4);
	ctx.fillText('zoom '+ scaleDenominator2zoom(scale), dw+tw/2, dh+3*th/4);
    }

    // the actual paper size rectangle frame
    ctx.strokeStyle = "#000000";
    ctx.setLineDash([]);
    ctx.strokeRect(dw, dh, tw, th);

    ctx.restore();
}

function enable_button(buttons, txt)
{
    for (button of buttons)
    {
	button.classList.remove("btn-success");
	button.classList.remove("btn-outline-secondary");
	button.classList.add("btn-primary");

	button.removeAttribute("disabled");

	button.setAttribute("title", txt);
    }
}

function disable_button(buttons)
{
    for (button of buttons)
    {
	button.classList.remove("btn-primary");
	button.classList.remove("btn-success");
	button.classList.add("btn-outline-secondary");

	button.setAttribute("disabled", "");

	button.setAttribute("title", "");
    }
}

function mark_button(buttons)
{
    for (button of buttons)
    {
	button.classList.remove("btn-primary");
	button.classList.add("btn-success");
    }
}

function unmark_button(buttons)
{
    for (button of buttons)
    {
	button.classList.remove("btn-success");
	button.classList.add("btn-primary");
    }
}

function disable_all_papersizes()
{
    $('.papersize:enabled').each(function(index) {
	disable_button($(this));
    });
}

function disable_papersize(w,h)
{
    var id = ".papersize_" + w + "_" + h;

    var buttons = $(id);

    if (buttons.length) {
	disable_button(buttons);
    }
}

function enable_papersize(w, h, txt)
{
    var id;

    if (w >0 && h>0) {
	id = ".papersize_" + w + "_" + h;
    } else {
	id = ".papersize_best_fit";
	w = parseInt($("#best_width").text());
	h = parseInt($("#best_height").text());
    }

    var buttons = $(id);

    if (buttons.length) {
	enable_button(buttons, txt);
    }
}


function scaleDenominator2zoom(scale_denom)
{
    if (scale_denom < 500)       return 20;
    if (scale_denom < 1250)      return 19;
    if (scale_denom < 2500)      return 18;
    if (scale_denom < 5000)      return 17;
    if (scale_denom < 12500)     return 16;
    if (scale_denom < 25000)     return 15;
    if (scale_denom < 50000)     return 14;
    if (scale_denom < 100000)    return 13;
    if (scale_denom < 200000)    return 12;
    if (scale_denom < 400000)    return 11;
    if (scale_denom < 750000)    return 10;
    if (scale_denom < 1500000)   return 9;
    if (scale_denom < 3000000)   return 8;
    if (scale_denom < 6500000)   return 7;
    if (scale_denom < 12500000)  return 6;
    if (scale_denom < 25000000)  return 5;
    if (scale_denom < 50000000)  return 4;
    if (scale_denom < 100000000) return 3;
    if (scale_denom < 200000000) return 2;
    if (scale_denom < 500000000) return 1;
    return 0;
}
