<?php
require_once 'HTTP/Request2.php';

define('BASE_URL', 'https://api.get-map.org/apis/');

function api_call($url) 
{
  $request = new HTTP_Request2(BASE_URL . $url);

  $request->setMethod(HTTP_Request2::METHOD_GET);
  
  $response = $request->send();
  $status = $response->getStatus();

  if ($status < 200 || $status > 299) {
	  echo "invalid HTTP response to '$url': $status\n";
	  echo $response->getBody();
	  exit(3);
  }

  return json_decode($response->getBody());
}

echo "PAPER FORMATS:\n";
$paper_formats = api_call('paper_formats');
foreach ($paper_formats AS $name => $format) 
  printf("%-10s: %4dx%4d mm²\n", $name, $format->width, $format->height);

echo "\nLAYOUTS\n";
$layouts = api_call('layouts');
foreach ($layouts as $name => $layout) 
  printf("%-25s: %s\n", $name, $layout->description);

echo "\nSTYLES\n";
$styles = api_call('styles');
foreach ($styles as $name => $style) 
  printf("%-25s: %s\n", $name, $style->description);

echo "\nOVERLAYS\n";
$overlays = api_call('overlays');
foreach ($overlays as $name => $overlay) 
  printf("%-25s: %s\n", $name, $overlay->description);
