<?php
// Ambil data dari API
$api_url = 'http://myweb.net:8081/results';
$response = file_get_contents($api_url);
$json = json_decode($response, true);

// Cek data
if (!$json || !isset($json['results'])) {
    die("Data tidak tersedia.");
}

$data = $json['results'];

// Proses data
$total_pengunjung = 0;
$emotion_count = [];         // ['happy' => 8, 'sad' => 3, ...]
$latest_by_emotion = [];     // ['happy' => '2025-04-06 00:21:51', ...]

foreach ($data as $entry) {
    $emotion = strtolower($entry['dominant_emotion']);
    $count = $entry['people_count'];
    $timestamp = $entry['created_at'];

    $total_pengunjung += $count;

    if (!isset($emotion_count[$emotion])) {
        $emotion_count[$emotion] = 0;
        $latest_by_emotion[$emotion] = $timestamp;
    }

    $emotion_count[$emotion] += $count;

    // Jika ada draw nanti, kita butuh waktu paling baru
    if (strtotime($timestamp) > strtotime($latest_by_emotion[$emotion])) {
        $latest_by_emotion[$emotion] = $timestamp;
    }
}

// Cari emosi dengan jumlah terbanyak
$max = max($emotion_count);
$emosi_terbanyak = [];

// Ambil semua yang jumlahnya sama dengan max (buat cek draw)
foreach ($emotion_count as $emotion => $count) {
    if ($count == $max) {
        $emosi_terbanyak[] = $emotion;
    }
}

// Jika cuma satu emosi, langsung ambil
if (count($emosi_terbanyak) == 1) {
    $dominant_emotion = $emosi_terbanyak[0];
} else {
    // Kalau draw, ambil yang waktu-nya paling baru
    $latest_time = 0;
    $dominant_emotion = '';
    foreach ($emosi_terbanyak as $emotion) {
        $time = strtotime($latest_by_emotion[$emotion]);
        if ($time > $latest_time) {
            $latest_time = $time;
            $dominant_emotion = $emotion;
        }
    }
}

// Ambil created_at paling baru dari data
$latest_created_at = max(array_column($data, 'created_at'));
$today = date('d/m/Y', strtotime($latest_created_at));

$emotion_display = ucfirst($dominant_emotion);
$emotion_img = "emoticon/" . $dominant_emotion . ".png";
?>
<!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<meta http-equiv="refresh" content="10">
	<title>Trendbox Dashboard</title>
	<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.5/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-SgOJa3DmI69IUzQ2PVdRZhwQ+dy64/BUtbMJw1MZ8t5HZApcHrRKUc4W0kG879m7" crossorigin="anonymous">
</head>
<body>
	<header>
		<nav class="navbar" style="border-bottom: 1px solid black;">
		  <div class="container-fluid">
		    <span class="navbar-brand mb-0 h1" style="font-size: 24pt;">Trendbox</span>
		  </div>
		</nav>
	</header>
	<main class="container mt-5">
		<div class="row">
			<div class="col-sm-8 mb-4">
				<h1 class="text-center">Data (Sample)</h1>
				<div class="p-4" style="border: 1px solid black; box-shadow: 3px 4px black;">
					<p><strong>Tanggal:</strong> <span style="font-family: monospace;"><?php echo $today; ?></span></p>
					<hr/>
					<p><strong>Jumlah Pengunjung:</strong> <?php echo $total_pengunjung; ?></p>
					<hr/>
					<p><strong>Emosi Dominan:</strong> <mark><?php echo $emotion_display; ?></mark></p>
				</div>
			</div>
			<div class="col-sm-4 text-center mb-4">
				<h1>Pengunjung</h1>
				<div class="p-4" style="border: 1px solid black; box-shadow: 3px 4px black;">
					<img src="<?php echo $emotion_img; ?>" alt="<?php echo $emotion_display; ?> face" class="img-thumbnail">
					<h4 class="text-center"><?php echo $emotion_display; ?></h4>
				</div>
			</div>
		</div>
	</main>
	<footer></footer>
	<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.5/dist/js/bootstrap.bundle.min.js" crossorigin="anonymous"></script>
</body>
</html>
