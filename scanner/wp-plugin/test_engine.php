#!/usr/bin/env php
<?php
// test_engine.php — standalone harness: exercises the plugin engine without WP.
// Usage: php test_engine.php  (loads engine.php, defines wp_* stubs)

error_reporting( E_ALL );

// The engine guards against direct access (correct WP behaviour); stub it.
if ( ! defined( 'ABSPATH' ) ) { define( 'ABSPATH', '/tmp/' ); }

function wp_remote_get( $url, $args = array() ) {
	$ctx = stream_context_create( array( 'http' => array(
		'method' => 'GET', 'timeout' => 20,
		'header' => "User-Agent: EAA-ComplianceScanner-WP/1.0\r\n",
		'ignore_errors' => true,
		'max_redirects' => 5,
	) ) );
	$body = @file_get_contents( $url, false, $ctx );
	if ( $body === false ) { return new WPError(); }
	$hdrs = function_exists( 'http_get_last_response_headers' ) ? http_get_last_response_headers() : null;
	$code = 200;
	if ( is_array( $hdrs ) && isset( $hdrs[0] ) && preg_match( '/HTTP\/\S+\s+(\d+)/', $hdrs[0], $m ) ) { $code = (int) $m[1]; }
	return array( 'body' => $body, 'response' => array( 'code' => $code ) );
}
class WPError { public function get_error_message() { return 'fetch failed'; } }
function is_wp_error( $x ) { return $x instanceof WPError; }
function wp_remote_retrieve_response_code( $r ) { return (int) ( is_array( $r ) ? $r['response']['code'] : 0 ); }
function wp_remote_retrieve_body( $r ) { return is_array( $r ) ? $r['body'] : ''; }

require __DIR__ . '/eaa-compliance-scanner/engine.php';

$engine = new EAA_Scanner_Engine();

$bad = <<<'HTML'
<!doctype html><html><head><meta charset="utf-8"></head>
<body style="background:#fff;color:#aaa">
<h2>Skipped heading start</h2><h4>skip again</h4>
<img src="/pic.png"><img src="/logo.png" alt="Logo">
<form>
<input type="text" name="email" placeholder="Email">
<select name="topic"><option>1</option></select>
<textarea name="msg"></textarea>
<input type="hidden" name="csrf">
<input type="text" id="ok" aria-label="OK field">
</form>
<a href="/x"><img src="icon.png"></a>
<button></button><button aria-label="close">✕</button>
<a href="/y" target="_blank">Docs</a>
<iframe src="https://embed.example"></iframe>
<table><tr><td>a</td></tr></table>
<div id="dup"></div><span id="dup"></span>
<span style="color:#999;font-weight:bold">low contrast text</span>
<span aria-hidden="true"><a href="/z" tabindex="0">hidden link</a></span>
<p style="font-size:12px">px1</p><p style="font-size:14px">px2</p><p style="font-size:16px">px3</p>
</body></html>
HTML;

$good = <<<'HTML'
<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Clean page</title><meta name="viewport" content="width=device-width, initial-scale=1">
</head><body style="background:#fff;color:#222">
<h1>Welcome</h1><h2>Section</h2>
<img src="/a.png" alt="A thing">
<form><label for="e">Email</label><input type="text" id="e" name="email"></form>
<a href="/x">Normal link</a><button>Go</button>
<iframe src="https://embed.example" title="Embed"></iframe>
<table><tr><th>H</th></tr><tr><td>d</td></tr></table>
</body></html>
HTML;

$fail = 0;

$r = $engine->scan_html( $bad );
echo "== BAD document ==\nscore={$r['score']} grade={$r['grade']}\n";
$ids = array_column( $r['findings'], 'rule_id' );
foreach ( $ids as $id ) { echo "  found: $id\n"; }

$expect_bad = array(
	'DOC_TITLE', 'HTML_LANG', 'VIEWPORT', 'HEADING_SKIP', 'HEADING_H1',
	'IMG_ALT', 'FORM_LABEL', 'LINK_TEXT', 'BUTTON_TEXT', 'TARGET_BLANK',
	'IFRAME_TITLE', 'TABLE_HEADER', 'DUP_ID', 'CONTRAST',
);
foreach ( $expect_bad as $want ) {
	if ( ! in_array( $want, $ids, true ) ) { echo "FAIL: missing $want\n"; $fail++; }
}

$r2 = $engine->scan_html( $good );
echo "\n== CLEAN document ==\nscore={$r2['score']} grade={$r2['grade']}\n";
if ( $r2['score'] !== 100 || $r2['findings'] ) { echo "FAIL: clean doc scored {$r2['score']} with findings\n"; $fail++; }

// live URL smoke test
$r3 = $engine->scan_url( 'https://example.com' );
echo "\n== example.com ==\nok=" . var_export( $r3['ok'], true ) . " score={$r3['score']}\n";
if ( ! $r3['ok'] ) { echo "FAIL: scan_url failed: {$r3['error']}\n"; $fail++; }

echo $fail ? "\n$fail FAILURES\n" : "\nALL PASS\n";
exit( $fail ? 1 : 0 );
