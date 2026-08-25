<?php
/**
 * EAA Compliance Scanner — universal accessibility checker engine (PHP).
 *
 * Port of scanner_core.py (the platform-independent core) to PHP. Scans raw
 * HTML against a WCAG 2.1 AA subset relevant to the European Accessibility
 * Act: 21 rules, same rule IDs and scoring as the web scanner at
 * hermes-passiv.pages.dev/scan.
 *
 * @package eaa-compliance-scanner
 * @version 1.1.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

final class EAA_Scanner_Engine {

	/** @var array<string,bool> duplicate id values seen */
	private $dup_ids = array();
	/** @var array<string,bool> ids already seen */
	private $ids_seen = array();

	/**
	 * Scan an HTML string; return the report as an associative array
	 * (same shape as scanner_core.scan_html).
	 */
	public function scan_html( string $html ): array {
		$this->dup_ids  = array();
		$this->ids_seen = array();

		$findings = array();
		$add = function ( string $id, string $sev, string $msg, int $n, array $examples = array() ) use ( &$findings ) {
			if ( $n > 0 ) {
				$findings[] = array(
					'rule_id'  => $id,
					'severity' => $sev,
					'message'  => str_replace( '{n}', (string) $n, $msg ),
					'count'    => $n,
					'examples' => array_slice( array_map( function ( $e ) { return mb_substr( (string) $e, 0, 80 ); }, $examples ), 0, 3 ),
				);
			}
		};

		// --- single-pass tokeniser: tag events + the text that follows them --
		// One regex yields every event in document order: open/close tags and
		// text runs, so buffers (title/link/button/contrast) stay consistent.
		if ( ! preg_match_all(
			'/<(\/?)((?:script|style)\b|([a-zA-Z][a-zA-Z0-9]*)((?:"[^"]*"|\'[^\']*\'|[^>"\'])*)(\/?))>([^<]*)/',
			$html,
			$ev,
			PREG_SET_ORDER
		) ) {
			return $this->report( array(), array() );
		}

		$imgs_no_alt      = array();
		$img_alt_ok       = 0;
		$labels_for       = array();
		$inputs_unlab     = array();
		$empty_links      = 0;
		$empty_buttons    = 0;
		$headings         = array(); // list of levels
		$iframes_no_t     = array();
		$tables           = array(); // bool: has <th>
		$target_blank_bad = 0;
		$aria_hidden_focus= array();
		$fixed_px         = 0;
		// v1.2.0 rules (same set as npm core / Python core)
		$input_imgs_no_alt = 0;
		$videos_no_tracks  = array();
		$audio_no_alt      = array();
		$autoplay_bad      = array();
		$marquee_blink     = 0;
		$pos_tabindex      = 0;
		$title_present    = false;
		$lang_attr        = null;
		$viewport         = false;
		$form_count       = 0;

		$link_depth    = 0;
		$link_text_buf = '';
		$link_is_blank = false;
		$btn_depth     = 0;
		$btn_text_buf  = '';
		$h_level       = 0;

		// contrast: stack of [fg, bg, large] inherited through inline styles
		$style_stack = array();
		$low_pairs   = array();
		$seen_pairs  = array();

		foreach ( $ev as $m ) {
			$is_close   = $m[1] === '/';
			$raw_name   = isset( $m[2] ) ? $m[2] : '';
			$skip_media = ( strtolower( substr( $raw_name, 0, 6 ) ) === 'script' || strtolower( substr( $raw_name, 0, 5 ) ) === 'style' );
			$text_after = isset( $m[6] ) ? html_entity_decode( $m[6], ENT_QUOTES | ENT_HTML5 ) : '';

			// ---- script/style contents must not be treated as page text ----
			if ( $skip_media && ! $is_close ) {
				continue; // their inner content is matched by later events? No:
				// our regex only splits on tags; script bodies contain no '<'
				// usually, so they'd arrive as text_after of this open tag.
				// We simply never append it below because we continue here.
			}
			if ( $skip_media && $is_close ) {
				continue;
			}

			if ( ! $is_close ) {
				$tag   = strtolower( $m[3] );
				$rawat = isset( $m[4] ) ? $m[4] : '';
				$self  = isset( $m[5] ) && $m[5] === '/';

				// parse attributes (first occurrence wins)
				$attrs = array();
				if ( preg_match_all( '/([a-zA-Z_:][-a-zA-Z0-9_:.]*)(\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|(\S+)))?/', $rawat, $am, PREG_SET_ORDER ) ) {
					foreach ( $am as $a ) {
						$name = strtolower( $a[1] );
						$val  = '';
						if ( isset( $a[3] ) && $a[3] !== '' ) { $val = $a[3]; }
						elseif ( isset( $a[4] ) && $a[4] !== '' ) { $val = $a[4]; }
						elseif ( isset( $a[5] ) && $a[5] !== '' ) { $val = $a[5]; }
						if ( ! isset( $attrs[ $name ] ) ) {
							$attrs[ $name ] = html_entity_decode( $val, ENT_QUOTES | ENT_HTML5 );
						}
					}
				}

				$id = isset( $attrs['id'] ) ? $attrs['id'] : '';
				if ( $id !== '' ) {
					if ( isset( $this->ids_seen[ $id ] ) ) { $this->dup_ids[ $id ] = true; }
					else { $this->ids_seen[ $id ] = true; }
				}

				$style = isset( $attrs['style'] ) ? $attrs['style'] : '';

				switch ( $tag ) {
					case 'html':
						$lang_attr = isset( $attrs['lang'] ) ? $attrs['lang'] : null;
						break;
					case 'meta':
						if ( strtolower( isset( $attrs['name'] ) ? $attrs['name'] : '' ) === 'viewport' ) { $viewport = true; }
						break;
					case 'img':
						$alt = isset( $attrs['alt'] ) ? trim( $attrs['alt'] ) : '';
						if ( $alt === '' ) {
							$src           = isset( $attrs['src'] ) ? $attrs['src'] : '';
							$path          = parse_url( $src, PHP_URL_PATH );
							$imgs_no_alt[] = mb_substr( ( $path === false || $path === null || $path === '' ) ? $src : $path, 0, 80 );
						} else {
							$img_alt_ok++;
						}
						break;
					case 'label':
						if ( ! empty( $attrs['for'] ) ) { $labels_for[ $attrs['for'] ] = true; }
						break;
					case 'input':
						$itype = strtolower( isset( $attrs['type'] ) ? $attrs['type'] : 'text' );
						if ( 'image' === $itype ) {
							$alt_img = isset( $attrs['alt'] ) ? trim( $attrs['alt'] ) : '';
							if ( '' === $alt_img ) { $input_imgs_no_alt++; }
							break;
						}
						if ( in_array( $itype, array( 'hidden', 'submit', 'button', 'reset' ), true ) ) { break; }
						if ( empty( $id ) || ! isset( $labels_for[ $id ] ) ) {
							if ( empty( $attrs['aria-label'] ) && empty( $attrs['aria-labelledby'] ) && empty( $attrs['title'] ) ) {
								$name           = isset( $attrs['name'] ) ? $attrs['name'] : ( isset( $attrs['placeholder'] ) ? $attrs['placeholder'] : '' );
								$inputs_unlab[] = mb_substr( "input[$itype] $name", 0, 60 );
							}
						}
						break;
					case 'select':
					case 'textarea':
						if ( empty( $id ) || ! isset( $labels_for[ $id ] ) ) {
							if ( empty( $attrs['aria-label'] ) && empty( $attrs['aria-labelledby'] ) && empty( $attrs['title'] ) ) {
								$inputs_unlab[] = mb_substr( $tag . '[text]', 0, 60 );
							}
						}
						break;
					case 'button':
						if ( $btn_depth === 0 ) {
							$has_aria = ! empty( $attrs['aria-label'] ) || ! empty( $attrs['title'] )
								|| ( isset( $attrs['aria-labelledby'] ) && $attrs['aria-labelledby'] !== '' );
							if ( ! $has_aria ) {
								$btn_depth    = 1;
								$btn_text_buf = '';
							} else {
								$btn_depth = -1; // aria-labelled sentinel: ignore until close
							}
						}
						break;
					case 'a':
						if ( $link_depth === 0 ) {
							$has_aria = ! empty( $attrs['aria-label'] )
								|| ( isset( $attrs['aria-labelledby'] ) && $attrs['aria-labelledby'] !== '' );
							$link_is_blank = ( isset( $attrs['target'] ) && $attrs['target'] === '_blank' );
							$link_text_buf = '';
							$link_depth    = $has_aria ? -1 : 1; // -1 sentinel: aria-labelled
						}
						break;
					case 'iframe':
						if ( empty( $attrs['title'] ) ) {
							$iframes_no_t[] = mb_substr( isset( $attrs['src'] ) ? $attrs['src'] : '', 0, 60 );
						}
						break;
					case 'table':
						$tables[] = false;
						break;
					case 'th':
						if ( $tables ) { $tables[ count( $tables ) - 1 ] = true; }
						break;
					case 'form':
						$form_count++;
						break;
					case 'video':
						$has_data_caps = isset( $attrs['data-captions-present'] );
						if ( ! $has_data_caps ) {
							$videos_no_tracks[] = mb_substr( isset( $attrs['src'] ) ? $attrs['src'] : '', 0, 60 );
						}
						if ( isset( $attrs['autoplay'] ) && ! isset( $attrs['muted'] ) ) {
							$autoplay_bad[] = 'video';
						}
						break;
					case 'audio':
						$lbl = mb_strtolower( ( isset( $attrs['aria-label'] ) ? $attrs['aria-label'] : '' ) . ' ' . ( isset( $attrs['title'] ) ? $attrs['title'] : '' ) );
						if ( ! preg_match( '/transcript|captions?|subtitle/', $lbl ) ) {
							$audio_no_alt[] = mb_substr( isset( $attrs['src'] ) ? $attrs['src'] : '', 0, 60 );
						}
						if ( isset( $attrs['autoplay'] ) && ! isset( $attrs['controls'] ) ) {
							$autoplay_bad[] = 'audio';
						}
						break;
					case 'track':
						if ( isset( $attrs['kind'] ) && preg_match( '/captions?|subtitles/i', $attrs['kind'] ) && $videos_no_tracks ) {
							array_pop( $videos_no_tracks );
						}
						break;
					case 'marquee': case 'blink':
						$marquee_blink++;
						break;
					case 'h1': case 'h2': case 'h3': case 'h4': case 'h5': case 'h6':
						$h_level = (int) substr( $tag, 1 );
						break;
					case 'title':
						if ( trim( $text_after ) !== '' ) { $title_present = true; }
						break;
				}

				// aria-hidden + focusable element
				if ( ( isset( $attrs['aria-hidden'] ) && $attrs['aria-hidden'] === 'true' )
					&& isset( $attrs['tabindex'] ) && $attrs['tabindex'] !== '-1'
					&& in_array( $tag, array( 'a', 'button', 'input', 'select', 'textarea' ), true ) ) {
					$aria_hidden_focus[] = $tag;
				}

				// fixed px fonts
				if ( preg_match( '/font-size\s*:\s*\d+px/i', $style ) ) { $fixed_px++; }

				// v1.2.0: positive tabindex / text-decoration blink
				if ( isset( $attrs['tabindex'] ) && preg_match( '/^\s*(\d+)\s*$/', $attrs['tabindex'], $tm ) && (int) $tm[1] > 0 ) { $pos_tabindex++; }
				if ( preg_match( '/text-decoration\s*:\s*blink/i', $style ) ) { $marquee_blink++; }

				// inline style inheritance for contrast checks
				list( $pfg, $pbg, $plarge ) = $style_stack ? $style_stack[ count( $style_stack ) - 1 ] : array( '', '', false );
				$fg = $pfg; $bg = $pbg; $large = $plarge;
				if ( preg_match( '/(?:^|;)\s*color\s*:\s*([^;!]+)/i', $style, $cm ) ) { $fg = trim( $cm[1] ); }
				if ( preg_match( '/background(?:-color)?\s*:\s*([^;!]+)/i', $style, $bm ) ) {
					$v = trim( $bm[1] );
					if ( ! preg_match( '/url\(|gradient\(/i', $v ) ) { $bg = $v; }
				}
				if ( preg_match( '/font-size\s*:\s*(?:1[89]\d*[.,]?|2\d+|[3-9]\d+)\s*px|font-size\s*:\s*(?:14|1[5-9]|[2-9]\d+(?:\.\d+)?)\s*pt|font-weight\s*:\s*(?:bold|[6-9]00)/i', $style ) ) { $large = true; }
				if ( ! $self && ! in_array( $tag, array( 'img', 'br', 'hr', 'input', 'meta', 'link', 'source', 'track', 'wbr', 'area', 'base', 'col', 'embed', 'param' ), true ) ) {
					$style_stack[] = array( $fg, $bg, $large, $tag );
				}

				// text directly inside this element (link/button/title handled above)
				if ( $link_depth === 1 ) { $link_text_buf .= $text_after; }
				if ( $btn_depth === 1 ) { $btn_text_buf .= $text_after; }

				// contrast check for the text following the opening tag
				if ( trim( $text_after ) !== '' && $style_stack ) {
					list( $cfg, $cbg, $clarge ) = $style_stack[ count( $style_stack ) - 1 ];
					if ( $cfg !== '' && $cbg !== '' ) {
						$f = $this->parse_color( $cfg );
						$b = $this->parse_color( $cbg );
						if ( $f && $b ) {
							$ratio = $this->contrast_ratio( $f, $b );
							$key   = $cfg . '|' . $cbg . '|' . ( $clarge ? 'L' : 'N' );
							$thr   = $clarge ? 3.0 : 4.5;
							if ( $ratio !== null && $ratio < $thr && ! isset( $seen_pairs[ $key ] ) ) {
								$seen_pairs[ $key ] = true;
								$low_pairs[]        = sprintf( '%s on %s: %.2f:1 ("%s")', $cfg, $cbg, $ratio, mb_substr( trim( $text_after ), 0, 40 ) );
							}
						}
					}
				}
			} else {
				// closing tag
				$tag = strtolower( ltrim( $raw_name ) );
				switch ( $tag ) {
					case 'h1': case 'h2': case 'h3': case 'h4': case 'h5': case 'h6':
						if ( $h_level > 0 ) {
							$headings[] = $h_level;
							$h_level    = 0;
						}
						break;
					case 'button':
						if ( $btn_depth === 1 ) {
							$btn_depth = 0;
							if ( trim( $btn_text_buf ) === '' ) { $empty_buttons++; }
						} elseif ( $btn_depth === -1 ) {
							$btn_depth = 0;
						}
						break;
					case 'a':
						if ( $link_depth === 1 ) {
							$txt = trim( preg_replace( '/\s+/u', ' ', $link_text_buf ) ?? '' );
							$low = mb_strtolower( $txt );
							if ( $txt === '' ) {
								$empty_links++;
							} elseif ( $link_is_blank && strpos( $low, 'new window' ) === false && strpos( $low, 'new tab' ) === false ) {
								$target_blank_bad++;
							}
							$link_depth = 0;
						} elseif ( $link_depth === -1 ) {
							$link_depth = 0;
						}
						break;
				}
				// pop style stack if we opened this tag
				for ( $i = count( $style_stack ) - 1; $i >= 0; $i-- ) {
					if ( $style_stack[ $i ][3] === $tag ) {
						array_splice( $style_stack, $i );
						break;
					}
				}
			}
		}

		// --- build findings -------------------------------------------------
		$add( 'IMG_ALT', 'error', '{n} image(s) missing alt text', count( $imgs_no_alt ), $imgs_no_alt );
		$add( 'FORM_LABEL', 'error', '{n} form field(s) without an associated label', count( $inputs_unlab ), $inputs_unlab );
		$add( 'LINK_TEXT', 'error', '{n} link(s) with no accessible text', $empty_links );
		$add( 'BUTTON_TEXT', 'error', '{n} button(s) with no accessible text', $empty_buttons );
		$add( 'DUP_ID', 'error', '{n} duplicate id attribute value(s) (breaks label/aria references)', count( $this->dup_ids ), array_keys( $this->dup_ids ) );
		$add( 'TARGET_BLANK', 'warning', '{n} link(s) opening in a new window without warning the user', $target_blank_bad );
		$add( 'IFRAME_TITLE', 'warning', '{n} iframe(s) without a title attribute', count( $iframes_no_t ), $iframes_no_t );

		$tables_no_header = 0;
		foreach ( $tables as $has_th ) { if ( ! $has_th ) { $tables_no_header++; } }
		$add( 'TABLE_HEADER', 'warning', '{n} table(s) without header cells', $tables_no_header );

		if ( ! $title_present ) {
			$findings[] = array( 'rule_id' => 'DOC_TITLE', 'severity' => 'error', 'message' => 'page has no non-empty <title>', 'count' => 1, 'examples' => array() );
		}
		if ( empty( $lang_attr ) ) {
			$findings[] = array( 'rule_id' => 'HTML_LANG', 'severity' => 'error', 'message' => '<html> lacks a lang attribute', 'count' => 1, 'examples' => array() );
		}
		if ( ! $viewport ) {
			$findings[] = array( 'rule_id' => 'VIEWPORT', 'severity' => 'warning', 'message' => 'missing viewport meta (zoom disabled/unresponsive)', 'count' => 1, 'examples' => array() );
		}

		$h1_count = 0; $skips = 0; $prev = 0;
		foreach ( $headings as $lvl ) {
			if ( $lvl === 1 ) { $h1_count++; }
			if ( $prev && $lvl > $prev + 1 ) { $skips++; }
			$prev = $lvl;
		}
		if ( $h1_count === 0 ) {
			$findings[] = array( 'rule_id' => 'HEADING_H1', 'severity' => 'warning', 'message' => 'no <h1> found on the page', 'count' => 1, 'examples' => array() );
		}
		$add( 'HEADING_SKIP', 'warning', '{n} heading level skip(s) (e.g. h2 followed by h4)', $skips );

		if ( $fixed_px >= 3 ) {
			$findings[] = array( 'rule_id' => 'FIXED_PX_FONTS', 'severity' => 'notice', 'message' => "{$fixed_px} inline fixed px font-sizes (may block user zoom/text resize)", 'count' => $fixed_px, 'examples' => array() );
		}
		$add( 'ARIA_HIDDEN_FOCUS', 'error', '{n} element(s) with aria-hidden=true that are focusable', count( $aria_hidden_focus ), $aria_hidden_focus );

		// v1.2.0 rules
		$add( 'INPUT_TYPE_IMAGE_ALT', 'error', '{n} image submit button(s) (<input type=image>) without alt text (WCAG 1.1.1)', $input_imgs_no_alt );
		$add( 'VIDEO_TRACKS', 'error', '{n} video(s) without a captions/subtitles track (WCAG 1.2.2)', count( $videos_no_tracks ), $videos_no_tracks );
		$add( 'AUDIO_TRANSCRIPT', 'warning', '{n} audio element(s) with no indicated transcript or captions alternative (WCAG 1.2.1)', count( $audio_no_alt ), $audio_no_alt );
		$add( 'AUTOPLAY_MEDIA', 'error', '{n} media element(s) that autoplay without visible pause controls or muting (WCAG 1.4.2)', count( $autoplay_bad ), $autoplay_bad );
		if ( $marquee_blink > 0 ) {
			$findings[] = array( 'rule_id' => 'MARQUEE_BLINK', 'severity' => 'error',
				'message' => "{$marquee_blink} deprecated blinking/moving element(s) — cannot be paused by the user (WCAG 2.2.2)",
				'count' => $marquee_blink, 'examples' => array() );
		}
		if ( $pos_tabindex > 0 ) {
			$findings[] = array( 'rule_id' => 'POSITIVE_TABINDEX', 'severity' => 'warning',
				'message' => "{$pos_tabindex} element(s) with tabindex greater than 0 — breaks natural focus order (WCAG 2.4.3)",
				'count' => $pos_tabindex, 'examples' => array() );
		}

		if ( $low_pairs ) {
			$findings[] = array(
				'rule_id'  => 'CONTRAST',
				'severity' => 'error',
				'message'  => count( $low_pairs ) . ' text colour combination(s) below the WCAG AA contrast minimum (4.5:1 normal text, 3:1 large text)',
				'count'    => count( $low_pairs ),
				'examples' => array_slice( $low_pairs, 0, 3 ),
			);
		}

		return $this->report( $findings, array( 'tables' => count( $tables ), 'forms' => $form_count ) );
	}

	/** Score/grade/sort a findings list into the standard report shape. */
	private function report( array $findings, array $summary ): array {
		$errors = 0; $warnings = 0; $notices = 0;
		foreach ( $findings as $f ) {
			if ( $f['severity'] === 'error' ) { $errors++; }
			elseif ( $f['severity'] === 'warning' ) { $warnings++; }
			else { $notices++; }
		}
		$score = max( 0, 100 - $errors * 12 - $warnings * 5 - $notices * 2 );
		$grade = $score >= 90 ? 'A' : ( $score >= 75 ? 'B' : ( $score >= 55 ? 'C' : 'D' ) );

		usort( $findings, function ( $a, $b ) {
			$order = array_flip( array( 'error', 'warning', 'notice' ) );
			return ( $order[ $a['severity'] ] <=> $order[ $b['severity'] ] )
				?: strcmp( $a['rule_id'], $b['rule_id'] );
		} );

		return array(
			'ok'       => true,
			'standard' => 'EAA / WCAG 2.1 AA (subset)',
			'score'    => $score,
			'grade'    => $grade,
			'findings' => $findings,
			'summary'  => array_merge( array(
				'errors'   => $errors,
				'warnings' => $warnings,
				'notices'  => $notices,
			), $summary ),
		);
	}

	/** Parse a CSS colour to [r,g,b], or null if unparseable/transparent. */
	private function parse_color( string $s ): ?array {
		$s = strtolower( trim( $s ) );
		if ( $s === '' || in_array( $s, array( 'transparent', 'inherit', 'currentcolor', 'initial' ), true ) ) { return null; }
		if ( preg_match( '/^#([0-9a-f]{3})$/', $s, $m ) ) {
			$out = array();
			foreach ( str_split( $m[1] ) as $c ) { $out[] = hexdec( $c . $c ); }
			return $out;
		}
		if ( preg_match( '/^#([0-9a-f]{6})/', $s, $m ) ) {
			$h = $m[1];
			return array( hexdec( substr( $h, 0, 2 ) ), hexdec( substr( $h, 2, 2 ) ), hexdec( substr( $h, 4, 2 ) ) );
		}
		if ( preg_match( '/^rgba?\(([^)]+)\)$/', $s, $m ) ) {
			$p = array_map( 'trim', explode( ',', $m[1] ) );
			if ( count( $p ) >= 4 && (float) $p[3] < 0.9 ) { return null; }
			if ( count( $p ) < 3 ) { return null; }
			$out = array();
			for ( $i = 0; $i < 3; $i++ ) {
				$out[] = substr( $p[ $i ], -1 ) === '%' ? (float) $p[ $i ] * 2.55 : (float) $p[ $i ];
			}
			return $out;
		}
		$named = array(
			'white' => array(255,255,255), 'black' => array(0,0,0), 'red' => array(255,0,0),
			'green' => array(0,128,0), 'blue' => array(0,0,255), 'gray' => array(128,128,128),
			'grey' => array(128,128,128), 'silver' => array(192,192,192), 'yellow' => array(255,255,0),
			'orange' => array(255,165,0), 'navy' => array(0,0,128), 'teal' => array(0,128,128),
			'purple' => array(128,0,128), 'maroon' => array(128,0,0), 'olive' => array(128,128,0),
			'lime' => array(0,255,0), 'aqua' => array(0,255,255), 'cyan' => array(0,255,255),
			'fuchsia' => array(255,0,255), 'magenta' => array(255,0,255),
		);
		return isset( $named[ $s ] ) ? $named[ $s ] : null;
	}

	/** WCAG contrast ratio from two RGB triples. */
	private function contrast_ratio( array $f, array $b ): float {
		$lum = function ( array $rgb ): float {
			$ch = function ( float $c ): float {
				$c /= 255.0;
				return $c <= 0.04045 ? $c / 12.92 : pow( ( $c + 0.055 ) / 1.055, 2.4 );
			};
			return 0.2126 * $ch( $rgb[0] ) + 0.7152 * $ch( $rgb[1] ) + 0.0722 * $ch( $rgb[2] );
		};
		$lf = $lum( $f ); $lb = $lum( $b );
		return ( max( $lf, $lb ) + 0.05 ) / ( min( $lf, $lb ) + 0.05 );
	}

	/** Fetch a URL via wp_remote_get (redirect-following built in) and scan. */
	public function scan_url( string $url ): array {
		if ( ! preg_match( '#^https?://#i', $url ) ) {
			return array( 'ok' => false, 'error' => 'URL must start with http:// or https://', 'score' => null, 'findings' => array(), 'summary' => array() );
		}
		$res = wp_remote_get( $url, array(
			'timeout'             => 20,
			'redirection'         => 5,
			'user-agent'          => 'EAA-ComplianceScanner-WP/1.0 (+site audit)',
			'limit_response_size' => 2000000,
		) );
		if ( is_wp_error( $res ) ) {
			return array( 'ok' => false, 'error' => 'Could not fetch page: ' . $res->get_error_message(), 'score' => null, 'findings' => array(), 'summary' => array() );
		}
		$code = (int) wp_remote_retrieve_response_code( $res );
		if ( $code >= 400 ) {
			return array( 'ok' => false, 'error' => "Target returned HTTP {$code}", 'score' => null, 'findings' => array(), 'summary' => array() );
		}
		$body = wp_remote_retrieve_body( $res );
		if ( $body === '' ) {
			return array( 'ok' => false, 'error' => 'Page returned no HTML', 'score' => null, 'findings' => array(), 'summary' => array() );
		}
		$rep        = $this->scan_html( $body );
		$rep['url'] = $url;
		return $rep;
	}
}
