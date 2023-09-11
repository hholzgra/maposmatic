<?php
require_once 'HTTP/Request2.php';

define('BASE_URL', 'https://api.get-map.org/apis/');

$data = ['title'       => 'PHP Test',
         'bbox_bottom' => 52.00,
         'bbox_top'    => 52.02,
         'bbox_left'   => 8.50,
         'bbox_right'  => 8.52
        ];

$request = new HTTP_Request2(BASE_URL . "jobs");

$request->setMethod(HTTP_Request2::METHOD_POST)
		->setHeader('Content-type: application/json; charset=utf-8')
		->setBody(json_encode($data));

$response = $request->send();
$status   = $response->getStatus();

if ($status < 200 || $status > 299) {
    header("Content-type: text/plain");
    print_r($response->getBody());
    exit;
}

$reply = json_decode($response->getBody());

header("Location: " . $reply->interactive);
