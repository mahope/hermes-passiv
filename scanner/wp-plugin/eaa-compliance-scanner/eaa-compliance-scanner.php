<?php
/**
 * Plugin Name: EAA Compliance Scanner
 * Plugin URI:  https://hermes-passiv.pages.dev/scan
 * Description: Universal accessibility scanner (EAA / WCAG 2.1 AA subset, 15 rules). Scans your front page — or any URL — from the WordPress dashboard. Nothing is sent to third parties; the scan runs on your own server. Works with any theme.
 * Version:     1.1.0
 * Author:      ComplianceDocs
 * Author URI:  https://hermes-passiv.pages.dev
 * License:     MIT
 * Text Domain: eaa-compliance-scanner
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

require_once __DIR__ . '/engine.php';

const EAA_SCANNER_VERSION = '1.0.0';

/** Register admin menu. */
add_action( 'admin_menu', function () {
	add_management_page(
		'EAA Compliance Scanner',
		'EAA Scanner',
		'manage_options',
		'eaa-compliance-scanner',
		'eaa_scanner_render_admin'
	);
} );

/** Enqueue a tiny bit of CSS on our page only. */
add_action( 'admin_enqueue_scripts', function ( $hook ) {
	if ( $hook !== 'tools_page_eaa-compliance-scanner' ) { return; }
	echo '<style>
.eaa-wrap { max-width: 860px; }
.eaa-score { font-size: 42px; font-weight: 700; margin: 0; }
.eaa-A { color: #157a3c; } .eaa-B { color: #7a6415; }
.eaa-C { color: #a35a10; } .eaa-D { color: #a31515; }
.eaa-findings li { margin-bottom: 10px; }
.sev-error { color: #a31515; font-weight: 600; }
.sev-warning { color: #a35a10; } .sev-notice { color: #667; }
.eaa-fixtip { color: #445; font-size: 13px; display:block; margin-top:2px; }
</style>';
} );

/** The fix tips, same wording as the web scanner. */
function eaa_scanner_fix_tips(): array {
	return array(
		'IMG_ALT'           => 'Fix: add alt="description" to every meaningful image; use alt="" for purely decorative ones.',
		'FORM_LABEL'        => 'Fix: give every field a <label for="field-id">, or an aria-label attribute.',
		'LINK_TEXT'         => 'Fix: add descriptive text inside the link, or aria-label if it is icon-only.',
		'BUTTON_TEXT'       => 'Fix: add visible text or an aria-label to every button.',
		'DUP_ID'            => 'Fix: make every id value unique on the page.',
		'TARGET_BLANK'      => 'Fix: warn users the link opens in a new window (e.g. "(opens in new tab)") and add rel="noopener".',
		'DOC_TITLE'         => 'Fix: set a Site Title under Settings → General (or via SEO plugin).',
		'HTML_LANG'         => 'Fix: WordPress sets this automatically — a custom theme may be missing language_attributes().',
		'VIEWPORT'          => 'Fix: add <meta name="viewport" content="width=device-width, initial-scale=1"> in the theme header.',
		'HEADING_H1'        => 'Fix: add one descriptive <h1> as the main page heading.',
		'HEADING_SKIP'      => 'Fix: do not skip heading levels — nest h2 under h1, h3 under h2, etc.',
		'IFRAME_TITLE'      => 'Fix: add a title attribute describing the iframe content.',
		'TABLE_HEADER'      => 'Fix: use <th> for header cells in data tables.',
		'ARIA_HIDDEN_FOCUS' => 'Fix: remove aria-hidden from focusable elements, or add tabindex="-1".',
		'CONTRAST'          => 'Fix: darken the text colour or lighten the background until the contrast ratio is at least 4.5:1 (3:1 for large text). Check it at webaim.org/resources/contrastchecker.',
	);
}

/** Render the admin page. */
function eaa_scanner_render_admin() {
	if ( ! current_user_can( 'manage_options' ) ) {
		wp_die( 'Insufficient permissions.' );
	}

	$engine = new EAA_Scanner_Engine();
	$result = null;
	$scanned_url = '';

	if ( isset( $_POST['eaa_nonce'] ) && wp_verify_nonce( sanitize_key( $_POST['eaa_nonce'] ), 'eaa_scan' ) ) {
		$url = isset( $_POST['eaa_url'] ) ? esc_url_raw( wp_unslash( $_POST['eaa_url'] ) ) : '';
		if ( $url === '' ) {
			$url = home_url( '/' );
		}
		if ( ! preg_match( '#^https?://#i', $url ) ) {
			echo '<div class="notice notice-error"><p>URL must start with http:// or https://.</p></div>';
		} else {
			$result      = $engine->scan_url( $url );
			$scanned_url = $url;
		}
	}
	?>
	<div class="wrap eaa-wrap">
		<h1>EAA Compliance Scanner <span style="font-size:13px;color:#667">v<?php echo esc_html( EAA_SCANNER_VERSION ); ?></span></h1>
		<p>Universal accessibility check against an EAA / WCAG 2.1 AA subset
		(15 rules). Runs entirely on this server — no data leaves your site.</p>

		<form method="post" action="">
			<?php wp_nonce_field( 'eaa_scan', 'eaa_nonce' ); ?>
			<p>
				<label for="eaa_url"><strong>Page URL to scan</strong><br>
				<input type="url" id="eaa_url" name="eaa_url" size="60"
					placeholder="<?php echo esc_attr( home_url( '/' ) ); ?>"
					value="<?php echo esc_attr( $scanned_url ); ?>"></label>
			</p>
			<p><button type="submit" class="button button-primary button-hero">Scan now</button></p>
			<p class="description">Leave empty to scan this site's front page.</p>
		</form>

		<?php if ( is_array( $result ) && isset( $result['ok'] ) && ! $result['ok'] ) : ?>
			<div class="notice notice-error"><p><strong>Scan failed.</strong>
				<?php echo esc_html( $result['error'] ); ?></p></div>
		<?php elseif ( is_array( $result ) && $result['ok'] ) : ?>
			<hr>
			<h2>Result <?php echo $scanned_url ? '— ' . esc_html( $scanned_url ) : ''; ?></h2>
			<div style="text-align:center;padding:16px;background:#f6f8fa;border:1px solid #dfe3e8;border-radius:10px">
				<p class="eaa-score eaa-<?php echo esc_attr( $result['grade'] ); ?>">
					<?php echo esc_html( $result['score'] ); ?>/100 — Grade <?php echo esc_html( $result['grade'] ); ?>
				</p>
				<p><?php echo (int) $result['summary']['errors']; ?> error(s),
				   <?php echo (int) $result['summary']['warnings']; ?> warning(s)</p>
			</div>
			<?php if ( empty( $result['findings'] ) ) : ?>
				<p>🎉 No issues found by automated checks.</p>
			<?php else : ?>
				<ul class="eaa-findings">
					<?php foreach ( $result['findings'] as $f ) :
						$tips = eaa_scanner_fix_tips(); ?>
						<li>
							<span class="sev-<?php echo esc_attr( $f['severity'] ); ?>"><?php echo esc_html( $f['message'] ); ?></span>
							<span class="eaa-fixtip"><?php echo esc_html( isset( $tips[ $f['rule_id'] ] ) ? $tips[ $f['rule_id'] ] : '' ); ?></span>
							<?php if ( ! empty( $f['examples'] ) ) : ?>
								<em style="color:#667;font-size:12px">e.g. <?php echo esc_html( implode( ', ', array_slice( $f['examples'], 0, 3 ) ) ); ?></em>
							<?php endif; ?>
						</li>
					<?php endforeach; ?>
				</ul>
			<?php endif; ?>
			<p style="font-size:13px;color:#667"><strong>Honest limitation:</strong>
			automated checks catch roughly 30–40% of accessibility issues. The rest
			needs human judgement — see the
			<a href="https://hermes-passiv.pages.dev/" target="_blank">EAA Compliance guides and e-books</a>.</p>
		<?php endif; ?>
	</div>
	<?php
}
