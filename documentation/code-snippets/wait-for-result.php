<?php
require_once 'HTTP/Request2.php';

define('BASE_URL', 'https://api.get-map.org/apis/');

function api_GET($url) 
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

  return array($status, json_decode($response->getBody()));
}


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

echo $reply->interactive."\n";

$job_url = "/jobs/" .  $reply->id;

    echo "waiting ... ";
    sleep(15);
    list($status, $reply) = api_GET($job_url);

    switch ($status) {
    case 200:
        $done = 1;
        break;
    case 202:
        switch($reply->status) {
        case 0:
            echo "still in queue\n";
            break;
        case 1:
            echo "now being rendered\n";
            break;
        default:
            echo "unexpected status: ".$reply->status."\n";
            break;
        }
        break;
    default:
        die("unexpected HTTP status: $status");
        break;
    }
}

$pdf = basename($reply->files->pdf);
copy($reply->files->pdf, $pdf);

system("xdg-open $pdf");
rm($pdf);