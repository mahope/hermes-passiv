<?php
/**
 * Kør pluginens egen motor på et dokument og skriv hvilke regler der fyrede.
 *
 *   php tools/plugin_engine_probe.php <engine.php> <fixture.html>
 *
 * Stdout er én JSON-linje: `{"rule_ids": ["IMG_ALT", …], "count": 22}`.
 *
 * Hvorfor dette program findes: `tools/check_rule_claims.py` måler regeltallet
 * ved at læse koden. Det er en statisk tælling, og opgave 85 fandt 16 i det
 * publicerede zip mod 22 i kilden — fordi zip'en var en ældre build. En statisk
 * tælling kan altså finde en regel, motoren aldrig får til at fyre, og den
 * kan finde en motor, der aldrig lader en regel fyre. Kun en kørsel kan skelne
 * de to fra hinanden.
 *
 * Derfor læser dette **ikke** regel-id'erne i koden. Det indlæser motoren og
 * kalder `scan_html()` som en kunde ville, og læser svaret. `ABSPATH` defineres
 * først, fordi motoren ellers afslutter med `exit` — den er skrevet til at
 * dø af sig selv uden for WordPress.
 *
 * Ingen WordPress, ingen HTTP, ingen database: kun den ene klasse og et
 * dokument på disk.
 *
 * @package hermes-passiv
 */

ini_set( 'display_errors', 'stderr' );

if ( ! isset( $argv[1] ) || ! isset( $argv[2] ) ) {
	fwrite( STDERR, "brug: php plugin_engine_probe.php <engine.php> <fixture.html>\n" );
	exit( 2 );
}

$engine = $argv[1];
$fixture = $argv[2];

if ( ! is_readable( $engine ) ) {
	fwrite( STDERR, "kan ikke læse motoren: $engine\n" );
	exit( 2 );
}
if ( ! is_readable( $fixture ) ) {
	fwrite( STDERR, "kan ikke læse fixture: $fixture\n" );
	exit( 2 );
}

define( 'ABSPATH', __DIR__ . '/' );
require_once $engine;

$report = ( new EAA_Scanner_Engine() )->scan_html( file_get_contents( $fixture ) );

$ids = array();
foreach ( $report['findings'] as $f ) {
	$id = isset( $f['rule_id'] ) ? $f['rule_id'] : '';
	if ( $id !== '' && ! in_array( $id, $ids, true ) ) {
		$ids[] = $id;
	}
}
sort( $ids );

echo wp_json_encode_compat( array( 'rule_ids' => $ids, 'count' => count( $ids ) ) ), "\n";
exit( 0 );

/**
 * `wp_json_encode()` findes ikke uden for WordPress. Denne motor skal kunne
 * køre i en ren PHP-CLI, så den får sin egen — men kun fordi den skal kunne
 * køre der.
 */
function wp_json_encode_compat( $value ) {
	return json_encode( $value );
}
