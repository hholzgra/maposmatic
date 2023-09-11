<?php
require_once 'HTTP/Request2.php';

define('BASE_URL', 'https://api.get-map.org/apis/');
define('GPX_FILE', 'A1.gpx');

$data = [];

$request = new HTTP_Request2(BASE_URL . "jobs");

$request->setMethod(HTTP_Request2::METHOD_POST)
        ->addPostParameter('job', json_encode($data))
        ->addUpload('track', GPX_FILE, basename(GPX_FILE), 'application/gpx+xml');

$response = $request->send();
$status   = $response->getStatus();

echo "$status: ".$request->getBody()."\n";

if ($status < 200 || $status > 299) {
    header("Content-type: text/plain");
    print_r($response->getBody());
    exit;
}

$reply = json_decode($response->getBody());

echo "$status: ".$reply->interactive."\n";
