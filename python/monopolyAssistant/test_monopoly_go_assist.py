"""Offline unit tests for monopoly-go-assist, focused on the Pick a Box fix
(2026-09-15).

Pillow is required for frame-cache tests; no tesseract, adb or device is needed.
These test pure logic (_pick_a_box_ocr_matches) and the tap/poll/retry
control flow of cmd_pick_a_box()/is_pick_a_box_screen() via monkeypatched
module functions, never a real screenshot. Pixel geometry and real OCR
accuracy against the game's actual font can only be confirmed live on the
deployment host against a real device/screenshot - see RULES.md.

Run: python test_monopoly_go_assist.py
"""
import importlib.util
import importlib.machinery
import os
import unittest
from unittest import mock

# Exercise the automatic-mode regressions independently of real user preferences.
os.environ.setdefault('MONOPOLY_MULTIPLIER_MODE','max')

_SCRIPT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "monopoly-go-assist"
)


def _load_module():
    # The production script is deployed as an extensionless executable
    # (see README.md's "Deploying" section) - importlib.util lets tests
    # load it as a module without renaming/copying the real file.
    loader = importlib.machinery.SourceFileLoader("monopoly_go_assist", _SCRIPT_PATH)
    spec = importlib.util.spec_from_loader("monopoly_go_assist", loader)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mga = _load_module()


class PiOcrTest(unittest.TestCase):
    def test_each_image_gets_fresh_recognition_and_psm(self):
        from PIL import Image
        api = mock.Mock()
        api.GetUTF8Text.side_effect = ['x10\n', 'x1\n']
        with mock.patch.dict(os.environ, MONOPOLY_INPROCESS_OCR='1'), mock.patch.object(mga, '_ocr_api', api):
            self.assertEqual(mga.ocr_image(Image.new('RGB', (40, 20))), 'x10')
            self.assertEqual(mga.ocr_image(Image.new('RGB', (40, 20)), psm=11), 'x1')
        self.assertEqual(api.Clear.call_count, 2)
        self.assertEqual(api.ClearAdaptiveClassifier.call_count, 2)
        self.assertEqual(api.SetPageSegMode.call_args_list, [mock.call(7), mock.call(11)])
        self.assertEqual(api.Recognize.call_args_list, [mock.call(timeout=30000)] * 2)

    def test_timeout_never_returns_previous_text(self):
        from PIL import Image
        api = mock.Mock()
        api.Recognize.return_value = False
        with mock.patch.dict(os.environ, MONOPOLY_INPROCESS_OCR='1'), mock.patch.object(mga, '_ocr_api', api):
            self.assertEqual(mga.ocr_image(Image.new('RGB', (40, 20))), '')
        api.GetUTF8Text.assert_not_called()

    def test_native_tsv_keeps_collect_coordinates(self):
        from PIL import Image
        api = mock.Mock()
        api.GetTSVText.return_value = '5\t1\t1\t1\t1\t1\t400\t2100\t200\t50\t95\tCOLLECT\n'
        with mock.patch.dict(os.environ, MONOPOLY_INPROCESS_OCR='1'), mock.patch.object(mga, '_ocr_api', api):
            result = mga.ocr_image(Image.new('RGB', (1080, 2340)), psm=11, tsv=True)
        self.assertEqual(mga._find_collect_word_from_tsv(result), (500, 2125))

    def test_failed_native_engine_uses_cli(self):
        from PIL import Image
        api = mock.Mock()
        api.SetImage.side_effect = RuntimeError('engine failure')
        with mock.patch.dict(os.environ, MONOPOLY_INPROCESS_OCR='1'), mock.patch.object(mga, '_ocr_api', api), mock.patch.object(mga, 'sh', return_value=mock.Mock(stdout='x2\n')):
            self.assertEqual(mga.ocr_image(Image.new('RGB', (40, 20))), 'x2')

    def test_green_components_preserve_two_grid_step_connectivity(self):
        from PIL import Image, ImageDraw
        image = Image.new('RGB', (1080, 2340), 'black')
        draw = ImageDraw.Draw(image)
        draw.rectangle((300, 2120, 440, 2200), fill=(50, 220, 40))
        draw.rectangle((448, 2120, 600, 2200), fill=(50, 220, 40))
        with mock.patch.object(mga, 'screen_image', return_value=image):
            self.assertEqual(mga.find_green_button(), (450, 2128))
        # A larger gap must keep these individually too-narrow blobs separate.
        draw.rectangle((448, 2120, 451, 2200), fill='black')
        with mock.patch.object(mga, 'screen_image', return_value=image):
            self.assertIsNone(mga.find_green_button())


class PiFrameCacheTest(unittest.TestCase):
    def test_multiplier_cache_invalidates_on_new_frame(self):
        from PIL import Image
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp)/'first.png', Path(tmp)/'second.png'
            Image.new('RGB', (1080,2340), 'black').save(first)
            Image.new('RGB', (1080,2340), 'white').save(second)
            with mock.patch.object(mga, 'SCREENSHOT', str(first)), mock.patch.object(mga, '_ocr_cache', {}), mock.patch.object(mga, '_multiplier_preferred_box', None), mock.patch.object(mga, 'ocr_image', side_effect=['x10','x10','x1','x1']) as ocr:
                self.assertEqual(mga.get_multiplier()[0],10)
                self.assertEqual(mga.get_multiplier()[0],10)
                self.assertEqual(ocr.call_count,2)
                mga.SCREENSHOT=str(second)
                self.assertEqual(mga.get_multiplier()[0],1)
                self.assertEqual(ocr.call_count,4)

    def test_successful_crop_preferred_but_requires_new_pair(self):
        from PIL import Image
        with mock.patch.object(mga, 'screen_image', return_value=Image.new('RGB',(1080,2340))), mock.patch.object(mga, '_ocr_cache', {}), mock.patch.object(mga, '_multiplier_preferred_box', None), mock.patch.object(mga, 'ocr_image', side_effect=['x1','x4','x10','x10','x1','x4','x3','x3']) as ocr:
            self.assertEqual(mga.get_multiplier()[0],10)
            self.assertEqual(mga._multiplier_preferred_box,(700,1725,775,1780))
            mga._ocr_cache.clear()
            self.assertEqual(mga.get_multiplier()[0],3)
            self.assertEqual(ocr.call_count,8)

    def test_popup_observation_is_fast_but_back_still_waits(self):
        recovery=mga.PopupRecovery()
        with mock.patch.object(mga.time,'monotonic',return_value=0), mock.patch.object(mga,'report_phase'), mock.patch.object(mga.time,'sleep') as sleep, mock.patch.object(mga,'game_back') as back:
            recovery.handle()
            back.assert_not_called()
            sleep.assert_called_with(2)
        with mock.patch.object(mga.time,'monotonic',return_value=16), mock.patch.object(mga,'report_phase'), mock.patch.object(mga.time,'sleep'), mock.patch.object(mga,'game_back') as back:
            recovery.handle()
            back.assert_called_once()

    def test_diagnostic_retention_and_rate_limit(self):
        import tempfile
        from pathlib import Path
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/'screen.png';Image.new('RGB',(2,2)).save(src)
            with mock.patch.dict(os.environ, MONOPOLY_DIAGNOSTICS='1'), mock.patch('pathlib.Path.home', return_value=Path(tmp)), mock.patch.object(mga,'SCREENSHOT',str(src)), mock.patch.object(mga,'_diagnostic_times',{}), mock.patch.object(mga.time,'monotonic',return_value=100):
                for i in range(14):mga.record_diagnostic(f'reason_{i}')
                folder=Path(tmp)/'.local/state/monopoly-assist/diagnostics'
                self.assertEqual(len(list(folder.glob('*.png'))),12)
                with mock.patch.object(mga.shutil,'copyfile') as copy:
                    mga.record_diagnostic('reason_13');copy.assert_not_called()


class BuildBeforeRollTest(unittest.TestCase):
    def test_build_cooldown_leaves_rolling_available(self):
        with mock.patch.object(mga.time, 'monotonic', return_value=110), mock.patch.object(mga, '_last_build_visit', 100), mock.patch.object(mga, 'is_build_badge_present', return_value=True), mock.patch.object(mga, 'cmd_build') as build:
            self.assertFalse(mga.maybe_build_before_roll(1))
            build.assert_not_called()

    def test_failed_visit_requires_fresh_evaluation(self):
        with mock.patch.object(mga.time, 'monotonic', return_value=200), mock.patch.object(mga, '_last_build_visit', 0), mock.patch.object(mga, 'is_build_badge_present', return_value=True), mock.patch.object(mga, 'cmd_build', return_value=1) as build:
            self.assertTrue(mga.maybe_build_before_roll(1))
            build.assert_called_once()

    def test_main_loop_builds_before_multiplier_or_go(self):
        from contextlib import ExitStack
        with ExitStack() as stack:
            for name in ('handle_treasure', 'handle_house_choices', 'handle_railroad_chance', 'is_card_popup_screen', 'is_quit_dialog_present', 'is_collect_screen', 'is_pick_a_box_screen', 'is_bonus_roll_screen', 'is_color_wheel_screen', 'is_switch_opponent_menu', 'is_match3_screen', 'is_raid_screen', 'is_build_menu_open', 'maybe_check_wins'):
                stack.enter_context(mock.patch.object(mga, name, return_value=False))
            stack.enter_context(mock.patch.object(mga, 'screenshot'))
            stack.enter_context(mock.patch.object(mga, 'get_roll_fill_ratio', return_value=0.9))
            build = stack.enter_context(mock.patch.object(mga, 'maybe_build_before_roll', side_effect=KeyboardInterrupt))
            multiplier = stack.enter_context(mock.patch.object(mga, '_multiplier_action'))
            roll = stack.enter_context(mock.patch.object(mga, '_roll_action'))
            mga.cmd_loop()
            build.assert_called_once_with(0)
            multiplier.assert_not_called()
            roll.assert_not_called()


class ColorWheelTitleTest(unittest.TestCase):
    def setUp(self):
        mga._ocr_cache.clear()
        patcher = mock.patch.object(mga, 'ocr_image', return_value='')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_gallery_badge_is_not_a_color_wheel(self):
        from PIL import Image
        image = Image.new('RGB', (1080, 2340), (116, 160, 94))
        with mock.patch.object(mga, 'screen_image', return_value=image), \
             mock.patch.object(mga, 'ocr_region', return_value='NET WORTH GALLERY'):
            self.assertFalse(mga.is_color_wheel_screen())

    def test_color_wheel_requires_its_exact_title(self):
        from PIL import Image
        image = Image.new('RGB', (1080, 2340), (116, 160, 94))
        with mock.patch.object(mga, 'screen_image', return_value=image):
            for title in ('COLOR WHEEL', 'Color\nWheel'):
                with mock.patch.object(mga, 'ocr_region', side_effect=[
                        '', title, '/ SPIN \\', '1 spin left']):
                    self.assertTrue(mga.is_color_wheel_screen())
            for title in ('', 'SPIN', 'BUY SPINS $4.99', 'NET WORTH GALLERY',
                          'ULYSSES TRAVELS 13/30'):
                with mock.patch.object(mga, 'ocr_region', return_value=title):
                    self.assertFalse(mga.is_color_wheel_screen())

    def test_large_title_requires_both_complete_words_and_a_free_spin(self):
        from PIL import Image
        image = Image.new('RGB', (1080, 2340), (116, 160, 94))
        with mock.patch.object(mga, 'screen_image', return_value=image), \
             mock.patch.object(mga, 'ocr_image', side_effect=[
                 '* COLOR<_.', 'WHEEL:']), \
             mock.patch.object(mga, 'ocr_region', side_effect=[
                 '', '', '/ SPIN \\', '1 spin left']):
            self.assertTrue(mga.is_color_wheel_screen())

    def test_spin_prices_and_exhausted_or_unreadable_counts_are_rejected(self):
        from PIL import Image
        image = Image.new('RGB', (1080, 2340), (116, 160, 94))
        with mock.patch.object(mga, 'screen_image', return_value=image):
            for spin, count in [('SPIN $4.99', '1 spin left'),
                                ('SPIN', '0 spins left'), ('SPIN', '')]:
                with mock.patch.object(mga, 'ocr_region', side_effect=[
                        '', 'COLOR WHEEL', spin, count]):
                    self.assertFalse(mga.is_color_wheel_screen())

    def test_confirmed_board_skips_expensive_wheel_title_ocr(self):
        from PIL import Image
        image = Image.new('RGB', (1080, 2340), (116, 160, 94))
        with mock.patch.object(mga, 'screen_image', return_value=image), \
             mock.patch.object(mga, 'ocr_region',
                               return_value='WINS BUILD ALBUM FRIENDS') as ocr, \
             mock.patch.object(mga, 'ocr_image') as mask_ocr:
            self.assertFalse(mga.is_color_wheel_screen())
        ocr.assert_called_once_with((0, 2200, 1080, 2260), psm=7)
        mask_ocr.assert_not_called()


class HalloweenHouseTest(unittest.TestCase):
    def test_main_board_footer_rejects_build_green_sparkles(self):
        from PIL import Image
        image = Image.new('RGB', (1080,2340), (0,255,0))
        with mock.patch.object(mga,'screen_image',return_value=image), mock.patch.object(mga,'ocr_region',return_value='28/60 WINS BUILD ALBUM FRIENDS'):
            self.assertFalse(mga.is_build_menu_open())
        self.assertFalse(mga._main_board_footer_matches('LONDON 28/30'))
        self.assertFalse(mga._main_board_footer_matches('WINS ALBUM FRIENDS'))

    def test_main_board_navigation_excludes_build_when_dice_ocr_is_missing(self):
        from PIL import Image
        # Captured main-board OCR omitted the readable 265/70 dice pill.
        # GO sparkles still satisfy the broad BUILD green-icon fallback.
        footer = 'WINS | BUILD | | ALBUM | FRIENDS'
        image = Image.new('RGB', (1080, 2340), (0, 255, 0))
        with mock.patch.object(mga, 'screen_image', return_value=image), \
             mock.patch.object(mga, 'ocr_region', return_value=footer):
            self.assertFalse(mga.is_build_menu_open())
        for incomplete in ('WINS BUILD ALBUM', 'BUILD ALBUM FRIENDS',
                           'WINS ALBUM FRIENDS', 'LONDON 28/30 BUILD'):
            self.assertFalse(mga._main_board_footer_matches(incomplete))

    def test_board_navigation_row_survives_sparkle_block_ocr_failure(self):
        from PIL import Image
        image = Image.new('RGB', (1080, 2340), (0, 255, 0))
        # The first video frame produced no block OCR; the text-only row
        # consistently read the four navigation labels across the animation.
        with mock.patch.object(mga, 'screen_image', return_value=image), \
             mock.patch.object(mga, 'ocr_region', side_effect=[
                 '', 'WINS BUILD | ALBUM FRIENDS']) as ocr:
            self.assertFalse(mga.is_build_menu_open())
        self.assertEqual(ocr.call_args_list[-1],
                         mock.call((0, 2200, 1080, 2260), psm=7))

    def test_wrapped_player_name_uses_block_ocr(self):
        with mock.patch.object(mga,'find_house_choices',return_value=list(mga._HOUSE_POINTS)), mock.patch.object(mga,'ocr_region',side_effect=['unreadable',"SublimeOsprey51\u2019s\nBoard"]) as ocr, mock.patch.object(mga,'tap') as tap, mock.patch.object(mga.time,'sleep'):
            self.assertTrue(mga.handle_house_choices())
            ocr.assert_called_with((190,200,650,315),psm=6)
            tap.assert_called_once_with(*mga._HOUSE_POINTS[0])

    def setUp(self):
        mga._house_attempts.clear();mga._house_header=None

    def tearDown(self):
        mga._house_attempts.clear();mga._house_header=None

    def test_header_and_multiple_targets_required(self):
        with mock.patch.object(mga,'find_house_choices',return_value=[(551,850)]), mock.patch.object(mga,'ocr_region',return_value="Victoria's Board"), mock.patch.object(mga,'tap') as tap:
            self.assertFalse(mga.handle_house_choices());tap.assert_not_called()
        with mock.patch.object(mga,'find_house_choices',return_value=list(mga._HOUSE_POINTS)), mock.patch.object(mga,'ocr_region',return_value='Buy rolls $4.99'), mock.patch.object(mga,'tap') as tap:
            self.assertFalse(mga.handle_house_choices());tap.assert_not_called()

    def test_bounded_taps_even_when_header_ocr_varies(self):
        with mock.patch.object(mga,'find_house_choices',return_value=list(mga._HOUSE_POINTS)), mock.patch.object(mga,'ocr_region',side_effect=["Victoria's Board "+str(i) for i in range(12)]), mock.patch.object(mga,'tap') as tap, mock.patch.object(mga.time,'sleep'):
            for _ in range(12):self.assertTrue(mga.handle_house_choices())
            self.assertEqual(tap.call_count,10)

    def test_known_event_animation_stays_out_of_purchase_path(self):
        mga._house_header="Victoria's Board"
        with mock.patch.object(mga,'find_house_choices',return_value=[]), mock.patch.object(mga,'ocr_region',return_value="Victoria's Board"), mock.patch.object(mga,'is_collect_screen',return_value=False), mock.patch.object(mga,'tap') as tap, mock.patch.object(mga.time,'sleep'):
            self.assertTrue(mga.handle_house_choices());tap.assert_not_called()

    def test_circle_geometry_and_absence(self):
        from PIL import Image,ImageDraw
        img=Image.new('RGB',(1080,2340),'black');draw=ImageDraw.Draw(img)
        for x,y in mga._HOUSE_POINTS:draw.ellipse((x-70,y-70,x+70,y+70),outline='white',width=10)
        with mock.patch.object(mga,'screen_image',return_value=img):self.assertEqual(len(mga.find_house_choices()),5)
        with mock.patch.object(mga,'screen_image',return_value=Image.new('RGB',(1080,2340),'black')):self.assertEqual(mga.find_house_choices(),[])


class HalloweenHeaderSeparatorTest(unittest.TestCase):
    def test_observed_wrapped_title_separator_selects_a_verified_house(self):
        mga._house_attempts.clear();mga._house_header=None
        with mock.patch.object(mga,'find_house_choices',return_value=list(mga._HOUSE_POINTS)), mock.patch.object(mga,'ocr_region',side_effect=['rt eerie eats rr Q',"’ AgileGopher42’s |\nBoard"]), mock.patch.object(mga,'tap') as tap, mock.patch.object(mga.time,'sleep'):
            self.assertTrue(mga.handle_house_choices())
            tap.assert_called_once_with(*mga._HOUSE_POINTS[0])
        mga._house_attempts.clear();mga._house_header=None

    def test_separator_acceptance_does_not_repair_words_or_authorize_purchase(self):
        for text in ["Player's |\nBoard", "Player’s Board"]:
            self.assertTrue(mga._house_board_title(text))
        for text in ['Buy rolls $4.99', 'BOARD', "Player's B|OARD", "Player's | BOARO", "Player's | Purchase Board"]:
            self.assertFalse(mga._house_board_title(text))


class SpookyExpressOverviewTest(unittest.TestCase):
    def setUp(self):mga._spooky_close_retry=0.0

    def test_only_small_footer_cross_is_accepted(self):
        from PIL import Image,ImageDraw
        image=Image.new('RGB',(1080,2340),(238,234,216));draw=ImageDraw.Draw(image)
        draw.line((519,2182,560,2230),fill=(185,182,168),width=12)
        draw.line((560,2182,519,2230),fill=(185,182,168),width=12)
        point=mga.spooky_express_close_point(image)
        self.assertIsNotNone(point);self.assertLess(abs(point[0]-540),3);self.assertLess(abs(point[1]-2206),3)
        draw.rectangle((500,2160,590,2250),fill=(185,182,168))
        self.assertIsNone(mga.spooky_express_close_point(image))

    def test_exact_event_and_progress_text_required(self):
        with mock.patch.object(mga,'screen_image'),mock.patch.object(mga,'spooky_express_close_point',return_value=(540,2206)):
            with mock.patch.object(mga,'ocr_region',side_effect=['SPOOKY EXPRESS FIRST CLASS','Reach 45\nto upgrade']):
                self.assertEqual(mga.spooky_express_overview(),(540,2206))
            for title,progress in [('SPOOKY EXPRESS','Buy upgrade $4.99'),('OTHER EXPRESS','Reach 45 to upgrade'),('SPOOKY EXPRES','Reach 45 to upgrade')]:
                with mock.patch.object(mga,'ocr_region',side_effect=[title,progress]):self.assertIsNone(mga.spooky_express_overview())

    def test_close_is_verified_and_failed_attempts_are_bounded(self):
        with mock.patch.object(mga,'spooky_express_overview',side_effect=[(540,2206),None]),mock.patch.object(mga,'tap',return_value=True) as tap,mock.patch.object(mga,'screenshot'),mock.patch.object(mga.time,'sleep'):
            self.assertTrue(mga.handle_spooky_express());tap.assert_called_once_with(540,2206)
        with mock.patch.object(mga,'spooky_express_overview',return_value=(540,2206)),mock.patch.object(mga,'tap',return_value=True) as tap,mock.patch.object(mga,'screenshot'),mock.patch.object(mga.time,'sleep'):
            self.assertTrue(mga.handle_spooky_express());self.assertEqual(tap.call_count,2)
            self.assertTrue(mga.handle_spooky_express());self.assertEqual(tap.call_count,2)


class PickABoxOcrMatchTest(unittest.TestCase):
    """_pick_a_box_ocr_matches() is a pure function extracted from
    is_pick_a_box_screen() specifically so its text-matching rule can be
    tested without mocking screenshot/OCR plumbing."""

    def test_matches_clean_text(self):
        self.assertTrue(mga._pick_a_box_ocr_matches("PICK A BOX"))

    def test_matches_case_insensitive(self):
        self.assertTrue(mga._pick_a_box_ocr_matches("pick a box"))

    def test_matches_with_surrounding_ocr_noise(self):
        self.assertTrue(mga._pick_a_box_ocr_matches("  PICK A BOX!\n"))

    def test_rejects_missing_box(self):
        self.assertFalse(mga._pick_a_box_ocr_matches("PICK A CARD"))

    def test_rejects_missing_pick(self):
        self.assertFalse(mga._pick_a_box_ocr_matches("OPEN THE BOX"))

    def test_rejects_unrelated_purchase_upsell_text(self):
        # Guards against ever matching a real-money upsell popup's text.
        self.assertFalse(
            mga._pick_a_box_ocr_matches("KEEP ROLLING! 420 dice $1.99")
        )

    def test_rejects_empty_string(self):
        self.assertFalse(mga._pick_a_box_ocr_matches(""))


class CollectOcrFallbackTest(unittest.TestCase):
    def _row(self, text, confidence="92.0", left=410, top=1800,
             width=260, height=80):
        return (f"5\t1\t1\t1\t1\t1\t{left}\t{top}\t{width}\t{height}\t"
                f"{confidence}\t{text}")

    def test_returns_center_for_exact_collect_word(self):
        point = mga._find_collect_word_from_tsv(self._row("COLLECT"))
        self.assertEqual(point, (540, 1840))

    def test_accepts_punctuation_and_case_noise(self):
        point = mga._find_collect_word_from_tsv(self._row("Collect!"))
        self.assertEqual(point, (540, 1840))

    def test_rejects_unrelated_or_partial_words(self):
        rows = "\n".join((self._row("COLLECTION"), self._row("COLLEC")))
        self.assertIsNone(mga._find_collect_word_from_tsv(rows))

    def test_rejects_top_hud_and_low_confidence_matches(self):
        rows = "\n".join((
            self._row("COLLECT", top=200),
            self._row("COLLECT", confidence="12.0"),
        ))
        self.assertIsNone(mga._find_collect_word_from_tsv(rows))

    def test_go_area_button_gate_accepts_center_collect_position(self):
        self.assertTrue(mga._is_go_area_button((538, 1894)))

    def test_go_area_button_gate_rejects_unrelated_green_shapes(self):
        self.assertFalse(mga._is_go_area_button((250, 1894)))
        self.assertFalse(mga._is_go_area_button((538, 1500)))
        self.assertFalse(mga._is_go_area_button(None))


class IsPickABoxScreenGatingTest(unittest.TestCase):
    """Regression test for the 2026-09-15 fix: is_pick_a_box_screen() used
    to require is_card_popup_screen() (dimmed board) to pass first, but a
    real live screenshot showed this event does NOT dim the board - it
    replaces the top bar with different background art - so that gate
    silently suppressed detection on every real occurrence. Must never be
    reintroduced without live pixel confirmation (see RULES.md)."""

    def setUp(self):
        self._orig_ocr_region = mga.ocr_region
        self._orig_is_card_popup_screen = mga.is_card_popup_screen

    def tearDown(self):
        mga.ocr_region = self._orig_ocr_region
        mga.is_card_popup_screen = self._orig_is_card_popup_screen

    def test_detects_even_when_board_is_not_dimmed(self):
        mga.is_card_popup_screen = lambda: False
        mga.ocr_region = lambda *a, **k: "PICK A BOX"
        self.assertTrue(mga.is_pick_a_box_screen())

    def test_does_not_match_unrelated_text_even_when_dimmed(self):
        mga.is_card_popup_screen = lambda: True
        mga.ocr_region = lambda *a, **k: "KEEP ROLLING! 420 dice $1.99"
        self.assertFalse(mga.is_pick_a_box_screen())


class CmdPickABoxTest(unittest.TestCase):
    """Control-flow tests for the tap/poll/retry logic, via monkeypatched
    module-level functions - no real adb/screenshot/OCR calls."""

    def setUp(self):
        self._orig_tap = mga.tap
        self._orig_screenshot = mga.screenshot
        self._orig_is_pick_a_box_screen = mga.is_pick_a_box_screen
        self._orig_is_collect_screen = mga.is_collect_screen
        self._orig_drain = mga._drain_collect_popups
        self.taps = []
        mga.tap = lambda x, y: self.taps.append((x, y))
        mga.screenshot = lambda: None

    def tearDown(self):
        mga.tap = self._orig_tap
        mga.screenshot = self._orig_screenshot
        mga.is_pick_a_box_screen = self._orig_is_pick_a_box_screen
        mga.is_collect_screen = self._orig_is_collect_screen
        mga._drain_collect_popups = self._orig_drain

    @mock.patch("time.sleep", lambda *a, **k: None)
    def test_taps_exactly_go_button_and_succeeds_when_screen_clears(self):
        mga.is_pick_a_box_screen = lambda: False  # cleared right away
        mga.is_collect_screen = lambda: False
        result = mga.cmd_pick_a_box()
        self.assertEqual(result, 0)
        # SAFETY-relevant: must tap the calibrated GO_BUTTON point only,
        # never a derived/guessed crate coordinate.
        self.assertEqual(self.taps, [mga.GO_BUTTON])
        self.assertEqual(mga.GO_BUTTON, (539, 1901))

    @mock.patch("time.sleep", lambda *a, **k: None)
    def test_reward_popup_after_tap_counts_as_success_and_is_drained(self):
        mga.is_pick_a_box_screen = lambda: True  # still "PICK A BOX" text
        mga.is_collect_screen = lambda: True  # but a reward popup showed up
        drained = []
        mga._drain_collect_popups = lambda *a, **k: drained.append(True)
        result = mga.cmd_pick_a_box()
        self.assertEqual(result, 0)
        self.assertEqual(len(self.taps), 1)
        self.assertEqual(drained, [True])

    @mock.patch("time.sleep", lambda *a, **k: None)
    def test_gives_up_after_bounded_retries_when_genuinely_stuck(self):
        # Screen never clears and no reward popup ever appears - must not
        # tap forever; must stop at exactly PICK_A_BOX_TAP_RETRIES taps.
        mga.is_pick_a_box_screen = lambda: True
        mga.is_collect_screen = lambda: False
        result = mga.cmd_pick_a_box()
        self.assertEqual(result, 1)
        self.assertEqual(len(self.taps), mga.PICK_A_BOX_TAP_RETRIES)
        self.assertTrue(all(t == mga.GO_BUTTON for t in self.taps))

    @mock.patch("time.sleep", lambda *a, **k: None)
    def test_clears_partway_through_a_poll_window_stops_tapping(self):
        # Screen stays on "PICK A BOX" for a couple of poll rounds (the
        # reveal animation) before actually clearing - must not re-tap
        # while it's merely still animating.
        state = {"polls": 0}

        def fake_is_pick_a_box_screen():
            state["polls"] += 1
            return state["polls"] < 3  # clears on the 3rd poll check

        mga.is_pick_a_box_screen = fake_is_pick_a_box_screen
        mga.is_collect_screen = lambda: False
        result = mga.cmd_pick_a_box()
        self.assertEqual(result, 0)
        self.assertEqual(len(self.taps), 1)  # only the one initial tap



class MiniGamePriorityTest(unittest.TestCase):
    def test_specific_events_preempt_false_build_in_both_loops(self):
        for backoff in (False, True):
            for event in ("is_pick_a_box_screen", "is_bonus_roll_screen"):
                with self.subTest(backoff=backoff, event=event):
                    from contextlib import ExitStack
                    with ExitStack() as stack:
                        for name in ("is_quit_dialog_present", "is_collect_screen",
                                     "is_color_wheel_screen", "is_switch_opponent_menu",
                                     "is_match3_screen", "is_raid_screen",
                                     "is_pick_a_box_screen", "is_bonus_roll_screen", "is_card_popup_screen"):
                            stack.enter_context(mock.patch.object(mga, name, return_value=name == event or name == "is_color_wheel_screen"))
                        build = stack.enter_context(mock.patch.object(mga, "is_build_menu_open", return_value=True))
                        tap = stack.enter_context(mock.patch.object(mga, "tap"))
                        pick = stack.enter_context(mock.patch.object(mga, "cmd_pick_a_box", return_value=0))
                        stack.enter_context(mock.patch.object(mga, "get_roll_fill_ratio", return_value=1))
                        stack.enter_context(mock.patch.object(mga, "_keep_screen_awake"))
                        stack.enter_context(mock.patch.object(mga.time, "sleep"))
                        stack.enter_context(mock.patch.object(mga, "screenshot", side_effect=[None, KeyboardInterrupt()]))
                        try:
                            if backoff:
                                mga.sleep_keeping_awake(1, interval_s=1)
                            else:
                                mga.cmd_loop()
                        except KeyboardInterrupt:
                            pass
                        build.assert_not_called()
                        if event == "is_pick_a_box_screen":
                            pick.assert_called_once()
                            tap.assert_not_called()
                        else:
                            tap.assert_called_once_with(*mga.BONUS_ROLL_BUTTON)
                            pick.assert_not_called()


class QuitDialogConfirmationTest(unittest.TestCase):
    def test_dimmed_wheel_or_board_cannot_match_quit_by_color_alone(self):
        import sys
        image = mock.Mock()
        image.open.return_value.convert.return_value.getpixel.return_value = (242, 184, 83)
        with mock.patch.object(mga, "screen_image", return_value=image.open.return_value.convert.return_value), mock.patch.object(mga, "is_card_popup_screen", return_value=True):
            for text, expected in [("COLOR WHEEL SPIN", False), ("", False),
                                   ("Would you like to quit the game? CANCEL", True)]:
                with self.subTest(text=text), mock.patch.object(mga, "ocr_region", return_value=text):
                    self.assertEqual(mga.is_quit_dialog_present(), expected)


class GetMultiplierParsingTest(unittest.TestCase):
    def test_loose_digits_never_override_failed_consensus(self):
        for text in ("4", "x4", "x20", "", "garbage"):
            with self.subTest(text=text), mock.patch.object(mga, "ocr_region", return_value=text) as loose, mock.patch.object(mga, "_multiplier_ocr_fallback", return_value=(None, "x1 / x4")):
                self.assertIsNone(mga.get_multiplier()[0])
                loose.assert_not_called()


class MultiplierFallbackTest(unittest.TestCase):
    def test_consensus_requires_two_complete_matching_readings(self):
        self.assertEqual(mga._multiplier_consensus(["x1", "x1"]), 1)
        self.assertEqual(mga._multiplier_consensus(["x20", "X20"]), 20)
        for readings in (["xt", "xt"], ["x1", "x2"], ["x1"], ["x0", "x0"],
                         ["x1001", "x1001"], ["x1 |", "x1"]):
            self.assertIsNone(mga._multiplier_consensus(readings))

    def test_unreadable_primary_uses_verified_fallback(self):
        with mock.patch.object(mga, "ocr_region", return_value="xt"), mock.patch.object(
                mga, "_multiplier_ocr_fallback", return_value=(1, "x1 / x1")):
            self.assertEqual(mga.get_multiplier()[0], 1)

    def test_consensus_overrides_primary_digit_misread(self):
        with mock.patch.object(mga, "ocr_region", return_value="x4"), mock.patch.object(
                mga, "_multiplier_ocr_fallback", return_value=(1, "x1 / x1")) as fallback:
            self.assertEqual(mga.get_multiplier()[0], 1)
            fallback.assert_called_once()


class MultiplierProbeTest(unittest.TestCase):
    """_probe_multiplier_max(): bounded, observed cycling to find the
    multiplier's actual current cap by tapping until the reading wraps
    back down. Never touches GO_BUTTON - only ever taps MULTIPLIER_BADGE."""

    def setUp(self):
        self._orig_tap = mga.tap
        self._orig_screenshot = mga.screenshot
        self._orig_get_multiplier = mga.get_multiplier
        self._orig_bound = mga.MULTIPLIER_MAX_PROBE_TAPS
        self.taps = []
        mga.tap = lambda x, y: self.taps.append((x, y))
        mga.screenshot = lambda: None
        for name in ("is_quit_dialog_present", "is_collect_screen", "is_pick_a_box_screen",
                     "is_bonus_roll_screen", "is_color_wheel_screen", "is_switch_opponent_menu",
                     "is_match3_screen", "is_raid_screen", "is_build_menu_open",
                     "is_card_popup_screen"):
            setattr(self, "_orig_" + name, getattr(mga, name))
            setattr(mga, name, (lambda: False))
        self._blocked_names = ("is_quit_dialog_present", "is_collect_screen", "is_pick_a_box_screen",
                                "is_bonus_roll_screen", "is_color_wheel_screen", "is_switch_opponent_menu",
                                "is_match3_screen", "is_raid_screen", "is_build_menu_open",
                                "is_card_popup_screen")

    def tearDown(self):
        mga.tap = self._orig_tap
        mga.screenshot = self._orig_screenshot
        mga.get_multiplier = self._orig_get_multiplier
        mga.MULTIPLIER_MAX_PROBE_TAPS = self._orig_bound
        for name in self._blocked_names:
            setattr(mga, name, getattr(self, "_orig_" + name))

    @mock.patch("time.sleep", lambda *a, **k: None)
    def test_climbs_detects_wrap_and_settles_back_at_true_max(self):
        # x1 -> tap -> x2 -> tap -> x3 -> tap -> x1 (wrap!) -> tap -> x2 -> tap -> x3 (back at max)
        readings = [(1, "x1"), (2, "x2"), (3, "x3"), (1, "x1"), (2, "x2"), (3, "x3")]
        mga.get_multiplier = mock.Mock(side_effect=readings)
        result = mga._probe_multiplier_max()
        self.assertEqual(result, 3)
        self.assertEqual(len(self.taps), 5)
        self.assertTrue(all(t == mga.MULTIPLIER_BADGE for t in self.taps))

    @mock.patch("time.sleep", lambda *a, **k: None)
    def test_action_with_real_probe_stays_at_maximum(self):
        # Exercise caller + actual probe, not a mocked probe that hides its taps.
        state = {"value": 1}
        def advance(x, y):
            self.assertEqual((x, y), mga.MULTIPLIER_BADGE)
            self.taps.append((x, y))
            state["value"] = {1: 2, 2: 3, 3: 1}[state["value"]]
        mga.tap = advance
        mga.get_multiplier = lambda: (state["value"], "x" + str(state["value"]))
        with mock.patch.dict(mga._multiplier_cache, {"max": None, "probed_at_tick": None}):
            self.assertEqual(mga._multiplier_action(0), 0)
            self.assertEqual(state["value"], 3)
            self.assertEqual(len(self.taps), 5)

    @mock.patch("time.sleep", lambda *a, **k: None)
    def test_initial_ocr_failure_taps_nothing(self):
        mga.get_multiplier = mock.Mock(return_value=(None, ""))
        result = mga._probe_multiplier_max()
        self.assertIsNone(result)
        self.assertEqual(self.taps, [])

    @mock.patch("time.sleep", lambda *a, **k: None)
    def test_ocr_failure_mid_probe_stops_rather_than_tapping_blind(self):
        mga.get_multiplier = mock.Mock(side_effect=[(2, "x2"), (None, "")])
        result = mga._probe_multiplier_max()
        self.assertIsNone(result)
        self.assertEqual(len(self.taps), 1)  # the one tap that led to the bad read, no more

    @mock.patch("time.sleep", lambda *a, **k: None)
    def test_popup_mid_probe_stops_without_tapping_through_it(self):
        mga.get_multiplier = mock.Mock(return_value=(1, "x1"))
        mga.is_card_popup_screen = lambda: True  # blocked from the very first check
        result = mga._probe_multiplier_max()
        self.assertIsNone(result)
        self.assertEqual(self.taps, [])

    @mock.patch("time.sleep", lambda *a, **k: None)
    def test_hard_bound_stops_tapping_even_without_a_wrap(self):
        # OCR always reports a strictly higher value - must not tap forever.
        mga.MULTIPLIER_MAX_PROBE_TAPS = 3
        mga.get_multiplier = mock.Mock(side_effect=[(1, ""), (2, ""), (3, ""), (4, ""), (5, "")])
        result = mga._probe_multiplier_max()
        self.assertEqual(len(self.taps), 3)
        self.assertIsNone(result)

    @mock.patch("time.sleep", lambda *a, **k: None)
    def test_never_taps_go_button(self):
        readings = [(1, "x1"), (2, "x2"), (1, "x1"), (2, "x2")]
        mga.get_multiplier = mock.Mock(side_effect=readings)
        mga._probe_multiplier_max()
        self.assertNotIn(mga.GO_BUTTON, self.taps)


class MultiplierActionCacheTest(unittest.TestCase):
    """_multiplier_action(): uses the cached cap from _probe_multiplier_max()
    instead of reprobing every tick, except when the live reading exceeds
    the cache or the periodic reprobe interval has elapsed."""

    def setUp(self):
        self._orig_cache = dict(mga._multiplier_cache)
        mga._multiplier_cache.pop("retry_after", None)
        self._orig_tap = mga.tap
        self._orig_get_multiplier = mga.get_multiplier
        self._orig_probe = mga._probe_multiplier_max
        self.taps = []
        mga.tap = lambda x, y: self.taps.append((x, y))

    def tearDown(self):
        mga._multiplier_cache.clear()
        mga._multiplier_cache.update(self._orig_cache)
        mga.tap = self._orig_tap
        mga.get_multiplier = self._orig_get_multiplier
        mga._probe_multiplier_max = self._orig_probe

    def test_ocr_failure_takes_no_action_and_does_not_probe(self):
        mga._multiplier_cache.update({"max": None, "probed_at_tick": None})
        mga.get_multiplier = lambda: (None, "")
        probe = mock.Mock()
        mga._probe_multiplier_max = probe
        result = mga._multiplier_action(tick=0)
        self.assertEqual(result, 1)
        probe.assert_not_called()
        self.assertEqual(self.taps, [])

    def test_successful_probe_does_not_tap_again_using_stale_reading(self):
        mga._multiplier_cache.update({"max": None, "probed_at_tick": None})
        mga.get_multiplier = lambda: (1, "x1")
        mga._probe_multiplier_max = mock.Mock(return_value=3)
        result = mga._multiplier_action(tick=0)
        self.assertEqual(result, 0)
        self.assertEqual(self.taps, [])
        self.assertEqual(mga._multiplier_cache["max"], 3)
        self.assertEqual(mga._multiplier_cache["probed_at_tick"], 0)

    def test_lower_reading_reprobes_changed_cap_before_roll(self):
        mga._multiplier_cache.update({"max": 20, "probed_at_tick": 0})
        mga.get_multiplier = lambda: (2, "x2")
        probe = mock.Mock(return_value=3)
        mga._probe_multiplier_max = probe
        result = mga._multiplier_action(tick=5)
        self.assertEqual(result, 0)
        probe.assert_called_once()
        self.assertEqual(self.taps, [])
        self.assertEqual(mga._multiplier_cache["max"], 3)

    def test_reading_above_cache_forces_reprobe(self):
        # e.g. a boosted-rewards event started showing a badge above what
        # was previously confirmed as the cap.
        mga._multiplier_cache.update({"max": 3, "probed_at_tick": 0})
        mga.get_multiplier = lambda: (5, "x5")
        mga._probe_multiplier_max = mock.Mock(return_value=10)
        result = mga._multiplier_action(tick=1)
        self.assertEqual(result, 0)
        self.assertEqual(mga._multiplier_cache["max"], 10)
        self.assertEqual(self.taps, [])  # probe already settled at maximum

    def test_reprobe_interval_elapsed_forces_reprobe(self):
        mga._multiplier_cache.update({"max": 3, "probed_at_tick": 0})
        mga.get_multiplier = lambda: (3, "x3")
        probe = mock.Mock(return_value=3)
        mga._probe_multiplier_max = probe
        result = mga._multiplier_action(tick=mga.MULTIPLIER_REPROBE_TICKS)
        self.assertEqual(result, 0)
        probe.assert_called_once()

    def test_at_confirmed_max_does_not_tap(self):
        mga._multiplier_cache.update({"max": 3, "probed_at_tick": 0})
        mga.get_multiplier = lambda: (3, "x3")
        mga._probe_multiplier_max = mock.Mock()
        result = mga._multiplier_action(tick=1)
        self.assertEqual(result, 0)
        self.assertEqual(self.taps, [])
        mga._probe_multiplier_max.assert_not_called()

    def test_failed_periodic_reprobe_does_not_tap_through_popup(self):
        mga._multiplier_cache.update({"max": 3, "probed_at_tick": 0})
        mga.get_multiplier = lambda: (2, "x2")
        mga._probe_multiplier_max = mock.Mock(return_value=None)
        result = mga._multiplier_action(tick=mga.MULTIPLIER_REPROBE_TICKS)
        self.assertEqual(result, 1)
        self.assertEqual(self.taps, [])
        self.assertIsNone(mga._multiplier_cache["max"])


    def test_failed_probe_cannot_repeat_immediately(self):
        mga._multiplier_cache.update({"max": None, "probed_at_tick": None})
        mga.get_multiplier = lambda: (3, "x3")
        probe = mock.Mock(return_value=None)
        mga._probe_multiplier_max = probe
        self.assertEqual(mga._multiplier_action(tick=0), 1)
        self.assertEqual(mga._multiplier_action(tick=0), 1)
        probe.assert_called_once()
        self.assertEqual(self.taps, [])


class MultiplierMaxCommandTest(unittest.TestCase):
    def setUp(self):
        self._orig_probe = mga._probe_multiplier_max
        self._orig_cache = dict(mga._multiplier_cache)
        mga._multiplier_cache.pop("retry_after", None)

    def tearDown(self):
        mga._probe_multiplier_max = self._orig_probe
        mga._multiplier_cache.clear()
        mga._multiplier_cache.update(self._orig_cache)

    def test_success_exit_code(self):
        mga._probe_multiplier_max = mock.Mock(return_value=3)
        self.assertEqual(mga.cmd_multiplier_max(), 0)
        mga._probe_multiplier_max.assert_called_once_with(respect_mode=False)

    def test_failure_exit_code(self):
        mga._probe_multiplier_max = mock.Mock(return_value=None)
        self.assertEqual(mga.cmd_multiplier_max(), 1)

    def test_does_not_touch_the_loop_cache(self):
        mga._multiplier_cache.update({"max": 3, "probed_at_tick": 0})
        mga._probe_multiplier_max = mock.Mock(return_value=7)
        mga.cmd_multiplier_max()
        self.assertEqual(mga._multiplier_cache["max"], 3)





class LowDiceAndFrameCacheTest(unittest.TestCase):
    def test_small_contiguous_fill_still_allows_roll(self):
        image = mock.Mock()
        image.getpixel.side_effect = lambda xy: (20, 200, 250) if 380 <= xy[0] < 389 and abs(xy[1]-2152) <= 2 else (90, 85, 60)
        with mock.patch.object(mga, "screen_image", return_value=image):
            self.assertGreaterEqual(mga.get_roll_fill_ratio(), mga.ROLL_RATIO_EMPTY)

    def test_empty_and_isolated_blue_noise_stay_empty(self):
        for points in (set(), {(380,2152)}, {(380,2152),(381,2152),(382,2152)}):
            image = mock.Mock()
            image.getpixel.side_effect = lambda xy: (20,200,250) if xy in points else (90,85,60)
            with mock.patch.object(mga, "screen_image", return_value=image):
                self.assertLess(mga.get_roll_fill_ratio(), mga.ROLL_RATIO_EMPTY)

    def test_frame_reused_and_replacement_invalidates_ocr(self):
        import tempfile
        from PIL import Image
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frame.png"
            Image.new("RGB", (2,2), "red").save(path)
            with mock.patch.object(mga, "SCREENSHOT", str(path)):
                first = mga.screen_image()
                self.assertIs(first, mga.screen_image())
                mga._ocr_cache["test"] = "old"
                replacement = Path(directory) / "next.png"
                Image.new("RGB", (2,2), "blue").save(replacement)
                os.replace(replacement, path)
                self.assertEqual(mga.screen_image().getpixel((0,0)), (0,0,255))
                self.assertFalse(mga._ocr_cache)

class EmptyDiceLoopTest(unittest.TestCase):
    def test_empty_dice_never_probe_or_tap(self):
        from contextlib import ExitStack
        with ExitStack() as stack:
            for name in ('is_quit_dialog_present','is_collect_screen','is_pick_a_box_screen',
                         'is_bonus_roll_screen','is_color_wheel_screen','is_switch_opponent_menu',
                         'is_match3_screen','is_raid_screen','is_build_menu_open','is_card_popup_screen','maybe_check_wins'):
                stack.enter_context(mock.patch.object(mga, name, return_value=False))
            stack.enter_context(mock.patch.object(mga, 'screenshot'))
            stack.enter_context(mock.patch.object(mga, 'get_roll_fill_ratio', return_value=0))
            stack.enter_context(mock.patch.object(mga, '_settle_before_long_backoff', return_value=True))
            stack.enter_context(mock.patch.object(mga, 'cleanup_temp_images'))
            waiting = stack.enter_context(mock.patch.object(mga, 'sleep_keeping_awake', side_effect=KeyboardInterrupt))
            probe = stack.enter_context(mock.patch.object(mga, '_multiplier_action'))
            tapping = stack.enter_context(mock.patch.object(mga, 'tap'))
            mga.cmd_loop()
            waiting.assert_called_once()
            probe.assert_not_called()
            tapping.assert_not_called()




class BuildRecoveryTest(unittest.TestCase):
    def setUp(self):
        mga._build_close_retry_after = 0
        self.back = mock.patch.object(mga, "game_back", return_value=False)
        self.back.start()
        self.addCleanup(self.back.stop)

    def test_named_footer_survives_price_ocr_failure(self):
        self.assertTrue(mga._build_footer_matches("LITTLE M'S ROOM 4/30"))
        self.assertTrue(mga._build_footer_matches("LONDON 30/30"))
        for text in ("7 Rolls ready in 30:00", "30/35", "3/60", "LONDON 31/30", "4/30"):
            self.assertFalse(mga._build_footer_matches(text))

    def test_close_retries_then_confirms(self):
        with mock.patch.object(mga, 'screenshot'), mock.patch.object(mga.time, 'sleep'), mock.patch.object(mga, 'is_build_menu_open', side_effect=[True, True, False]), mock.patch.object(mga, 'tap') as tap:
            self.assertEqual(mga.close_build_menu(), 0)
            self.assertEqual(tap.call_count, 2)
            tap.assert_called_with(*mga.BUILD_CLOSE_X)

    def test_close_failure_is_bounded(self):
        with mock.patch.object(mga, 'screenshot'), mock.patch.object(mga.time, 'sleep'), mock.patch.object(mga, 'is_build_menu_open', return_value=True), mock.patch.object(mga, 'tap') as tap:
            self.assertEqual(mga.close_build_menu(), 1)
            self.assertEqual(tap.call_count, 4)

    def test_persistent_badge_visit_respects_cooldown(self):
        with mock.patch.object(mga, 'screenshot'), mock.patch.object(mga, 'is_build_menu_open', return_value=False), mock.patch.object(mga, '_last_build_visit', 100), mock.patch.object(mga.time, 'monotonic', return_value=110), mock.patch.object(mga, 'tap') as tap:
            self.assertEqual(mga.cmd_build(), 0)
            tap.assert_not_called()

    def test_leaving_build_stops_card_taps(self):
        with mock.patch.object(mga, 'screenshot'), mock.patch.object(mga.time, 'sleep'), mock.patch.object(mga, '_last_build_visit', 0), mock.patch.object(mga, 'is_build_menu_open', side_effect=[True, True, False]), mock.patch.object(mga, 'tap') as tap:
            self.assertEqual(mga.cmd_build(), 0)
            tap.assert_called_once_with(mga.BUILD_CARD_XS[0], mga.BUILD_CARD_Y)



class PurchaseLoopTests(unittest.TestCase):
    def setUp(self):
        patcher=mock.patch.object(mga,'is_wins_screen',return_value=False)
        patcher.start();self.addCleanup(patcher.stop)

    def test_close_attempts_are_bounded_and_reset_after_clear(self):
        guard = mga.PurchaseLoopGuard()
        with mock.patch.object(mga, 'tap') as tap, mock.patch.object(mga.time, 'sleep'):
            for _ in range(8):
                self.assertTrue(guard.handle(True, (100, 200)))
            self.assertEqual(tap.call_count, 2)
            self.assertFalse(guard.handle(False, None))
            guard.handle(True, (100, 200))
            self.assertEqual(tap.call_count, 3)
            self.assertTrue(all(c.args == (100, 200) for c in tap.call_args_list))

    def test_purchase_precedes_collect(self):
        with mock.patch.object(mga, 'screenshot', side_effect=[None, KeyboardInterrupt]), \
             mock.patch.object(mga, 'is_card_popup_screen', return_value=True), \
             mock.patch.object(mga, 'find_orange_x_button', return_value=(100,200)), \
             mock.patch.object(mga, 'is_collect_screen') as collect, \
             mock.patch.object(mga, 'tap') as tap, mock.patch.object(mga.time, 'sleep'):
            mga.cmd_loop()
            tap.assert_called_once_with(100,200)
            collect.assert_not_called()

    def test_reward_chain_stops_on_purchase(self):
        with mock.patch.object(mga, 'is_purchase_upsell_screen', return_value=True), \
             mock.patch.object(mga, 'find_collect_button') as find, mock.patch.object(mga, 'tap') as tap:
            mga._drain_collect_popups()
            find.assert_not_called()
            tap.assert_not_called()

    def test_unknown_popup_has_no_blind_taps(self):
        from contextlib import ExitStack
        with ExitStack() as stack:
            for name in ('is_quit_dialog_present','is_collect_screen','is_pick_a_box_screen',
                         'is_bonus_roll_screen','is_color_wheel_screen','is_switch_opponent_menu',
                         'is_match3_screen','is_raid_screen','is_build_menu_open','maybe_check_wins'):
                stack.enter_context(mock.patch.object(mga,name,return_value=False))
            stack.enter_context(mock.patch.object(mga,'is_card_popup_screen',return_value=True))
            stack.enter_context(mock.patch.object(mga,'find_orange_x_button',return_value=None))
            stack.enter_context(mock.patch.object(mga,'screenshot',side_effect=[None,KeyboardInterrupt]))
            stack.enter_context(mock.patch.object(mga.time,'sleep'))
            tap=stack.enter_context(mock.patch.object(mga,'tap'))
            mga.cmd_loop()
            tap.assert_not_called()

class BillingSafetyTests(unittest.TestCase):
    def test_game_focus_excludes_payment_unknown_and_other_apps(self):
        self.assertTrue(mga._game_has_focus('mCurrentFocus=Window{123 u0 com.scopely.monopolygo/Game}'))
        for value in ('', 'mCurrentFocus=null', 'mCurrentFocus=Window{123 u0 com.android.vending/Billing}',
                      'mCurrentFocus=Window{123 u0 com.scopely.monopolygo.fake/Game}'):
            self.assertFalse(mga._game_has_focus(value))

    def test_no_input_when_billing_has_focus(self):
        response=mock.Mock(returncode=0,stdout='mCurrentFocus=Window{123 u0 com.android.vending/Billing}')
        with mock.patch.object(mga.subprocess,'run',return_value=response), mock.patch.object(mga,'sh') as shell:
            self.assertFalse(mga.tap(540,2180))
            shell.assert_not_called()

    def test_price_and_locked_free_never_reward_labels(self):
        for label in ('$9.99','$14.99','FREE','BUY','Buy now','CLAIM $9.99',''):
            self.assertFalse(mga._safe_reward_label(label))
        for label in ('COLLECT','Go!','TAP TO CLAIM'):
            self.assertTrue(mga._safe_reward_label(label))

    def test_high_offer_close_button_is_found(self):
        from PIL import Image, ImageDraw
        frame=Image.new('RGB',(1080,2340),'black')
        ImageDraw.Draw(frame).ellipse((990,245,1050,305),fill=(255,100,0))
        with mock.patch.object(mga,'screen_image',return_value=frame):
            point=mga.find_orange_x_button()
        self.assertIsNotNone(point)
        self.assertTrue(990 <= point[0] <= 1050 and 245 <= point[1] <= 305)


class LogAuditRecoveryTests(unittest.TestCase):
    def setUp(self):
        patcher=mock.patch.object(mga,'is_wins_screen',return_value=False)
        patcher.start();self.addCleanup(patcher.stop)

    def test_raw_capture_rejects_partial_wrong_geometry_and_format(self):
        import struct
        for data in (b'', struct.pack('<IIII',1080,2340,1,0)+b'1234',
                     struct.pack('<IIII',2340,1080,1,0),
                     struct.pack('<IIII',1080,2340,2,0)):
            with self.assertRaises(ValueError):
                mga.decode_raw_frame(data)

    def test_raw_capture_accepts_both_header_sizes(self):
        import struct
        pixels = bytes([20,40,60,255]) * (1080*2340)
        for header in (struct.pack('<III',1080,2340,1), struct.pack('<IIII',1080,2340,1,0)):
            image=mga.decode_raw_frame(header+pixels)
            self.assertEqual(image.size,(1080,2340))
            self.assertEqual(image.getpixel((1079,2339)),(20,40,60))

    def test_disconnect_waits_without_capture_or_exit(self):
        with mock.patch.object(mga,'_continuous_mode',True), mock.patch.object(mga,'is_device_connected',return_value=False), mock.patch.object(mga.subprocess,'run') as run, mock.patch.object(mga.time,'sleep',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt): mga.screenshot()
            run.assert_not_called()

    def test_reconnect_resumes_with_valid_frame(self):
        import struct
        raw=struct.pack('<IIII',1080,2340,1,0)+bytes([1,2,3,255])*(1080*2340)
        focus=mock.Mock(returncode=0,stdout='mCurrentFocus=Window{123 u0 com.scopely.monopolygo/Game}')
        capture=mock.Mock(returncode=0,stdout=raw)
        with mock.patch.object(mga,'_continuous_mode',True), mock.patch.object(mga,'is_device_connected',side_effect=[False,True]), mock.patch.object(mga.subprocess,'run',side_effect=[focus,capture]), mock.patch.object(mga.time,'sleep') as sleep:
            mga.screenshot()
            sleep.assert_called_once_with(mga.DEVICE_POLL_S)
            self.assertEqual(mga.screen_image().getpixel((0,0)),(1,2,3))

    def test_payment_focus_waits_without_capture(self):
        focus=mock.Mock(returncode=0,stdout='mCurrentFocus=Window{123 u0 com.android.vending/Billing}')
        with mock.patch.object(mga,'_continuous_mode',True), mock.patch.object(mga,'is_device_connected',return_value=True), mock.patch.object(mga.subprocess,'run',return_value=focus) as run, mock.patch.object(mga.time,'sleep',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt): mga.screenshot()
            self.assertEqual(run.call_count,1)

    def test_dice_wait_closes_offer_before_reward_and_bounds_retries(self):
        with mock.patch.object(mga,'screenshot'), mock.patch.object(mga,'_keep_screen_awake'), mock.patch.object(mga.time,'sleep'), mock.patch.object(mga,'is_card_popup_screen',return_value=True), mock.patch.object(mga,'find_orange_x_button',return_value=(1000,270)), mock.patch.object(mga,'is_collect_screen') as collect, mock.patch.object(mga,'tap') as tap:
            mga.sleep_keeping_awake(90,15)
            self.assertEqual(tap.call_count,2)
            collect.assert_not_called()

    def test_dice_wait_unknown_popup_never_blind_taps(self):
        from contextlib import ExitStack
        with ExitStack() as stack:
            for name in ('screenshot','_keep_screen_awake'):
                stack.enter_context(mock.patch.object(mga,name))
            for name in ('is_quit_dialog_present','is_collect_screen','is_pick_a_box_screen','is_bonus_roll_screen','is_color_wheel_screen','is_switch_opponent_menu','is_match3_screen','is_raid_screen','is_build_menu_open','maybe_check_wins'):
                stack.enter_context(mock.patch.object(mga,name,return_value=False))
            stack.enter_context(mock.patch.object(mga,'is_card_popup_screen',return_value=True))
            stack.enter_context(mock.patch.object(mga,'find_orange_x_button',return_value=None))
            stack.enter_context(mock.patch.object(mga.time,'sleep'))
            tap=stack.enter_context(mock.patch.object(mga,'tap'))
            mga.sleep_keeping_awake(45,15)
            tap.assert_not_called()

    def test_build_failure_cannot_restart_taps_next_tick(self):
        with mock.patch.object(mga,'game_back',return_value=False), mock.patch.object(mga,'_build_close_retry_after',0), mock.patch.object(mga,'screenshot'), mock.patch.object(mga,'is_build_menu_open',return_value=True), mock.patch.object(mga.time,'sleep'), mock.patch.object(mga,'tap') as tap:
            mga.close_build_menu()
            mga.close_build_menu()
            self.assertEqual(tap.call_count,4)

class RaidReticleGeometryTests(unittest.TestCase):
    def test_red_ring_is_selected_instead_of_white_building_cross(self):
        from PIL import Image,ImageDraw
        image=Image.new('RGB',(1080,2340),(5,30,70));draw=ImageDraw.Draw(image)
        draw.ellipse((170,1405,330,1565),outline=(255,100,95),width=5)
        draw.line((920,1980,1060,2120),fill='white',width=35)
        draw.line((1060,1980,920,2120),fill='white',width=35)
        with mock.patch.object(mga,'screen_image',return_value=image):
            self.assertEqual(mga.find_raid_targets(),[(250,1485)])

    def test_white_cross_and_filled_red_square_are_not_reticles(self):
        from PIL import Image,ImageDraw
        image=Image.new('RGB',(1080,2340),'black');draw=ImageDraw.Draw(image)
        draw.line((920,1980,1060,2120),fill='white',width=35)
        draw.line((1060,1980,920,2120),fill='white',width=35)
        draw.rectangle((300,800,450,950),fill=(255,100,95))
        with mock.patch.object(mga,'screen_image',return_value=image):self.assertEqual(mga.find_raid_targets(),[])

    def test_legacy_white_circle_remains_supported(self):
        from PIL import Image,ImageDraw
        image=Image.new('RGB',(1080,2340),'black');ImageDraw.Draw(image).ellipse((200,800,350,950),outline='white',width=15)
        with mock.patch.object(mga,'screen_image',return_value=image):targets=mga.find_raid_targets()
        self.assertEqual(len(targets),1)
        self.assertLess(abs(targets[0][0]-275),3);self.assertLess(abs(targets[0][1]-875),3)


class ManualMultiplierModeTests(unittest.TestCase):
    def test_manual_changes_are_kept_without_probe_or_badge_taps(self):
        with mock.patch.dict(os.environ,MONOPOLY_MULTIPLIER_MODE='keep'),mock.patch.object(mga,'get_multiplier',side_effect=[(5,'x5'),(2,'x2')]),mock.patch.object(mga,'_probe_multiplier_max') as probe,mock.patch.object(mga,'tap') as tap:
            self.assertEqual(mga._multiplier_action(1),0);self.assertEqual(mga._multiplier_action(2),0)
            tap.assert_not_called();probe.assert_not_called()

    def test_keep_mode_does_not_guess_an_unreadable_badge_or_force_last_die(self):
        with mock.patch.dict(os.environ,MONOPOLY_MULTIPLIER_MODE='keep'),mock.patch.object(mga,'get_multiplier',return_value=(None,'')),mock.patch.object(mga,'tap') as tap:
            self.assertEqual(mga._multiplier_action(),1);tap.assert_not_called()
        with mock.patch.dict(os.environ,MONOPOLY_MULTIPLIER_MODE='keep'),mock.patch.object(mga,'get_multiplier',return_value=(3,'x3')),mock.patch.object(mga,'_last_die_detected',True),mock.patch.object(mga,'tap') as tap:
            self.assertEqual(mga._multiplier_action(),0);tap.assert_not_called()

    def test_mode_change_interrupts_an_automatic_probe_before_a_tap(self):
        with mock.patch.object(mga,'screenshot'),mock.patch.object(mga,'get_multiplier',return_value=(2,'x2')),mock.patch.object(mga,'_multiplier_mode',return_value='keep'),mock.patch.object(mga,'tap') as tap:
            self.assertIsNone(mga._probe_multiplier_max());tap.assert_not_called()

    def test_mode_change_also_stops_last_die_badge_adjustment(self):
        with mock.patch.object(mga,'_multiplier_mode',side_effect=['max','keep']),mock.patch.object(mga,'get_multiplier',return_value=(3,'x3')),mock.patch.object(mga,'_last_die_detected',True),mock.patch.object(mga,'tap') as tap:
            self.assertEqual(mga._multiplier_action(),0);tap.assert_not_called()

    def test_preferences_persist_and_preserve_other_settings(self):
        import tempfile,json
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp,mock.patch.dict(os.environ,{'MONOPOLY_PREFERENCES_FILE':str(Path(tmp)/'prefs.json')},clear=True):
            p=Path(tmp)/'prefs.json';p.write_text(json.dumps({'other':'retained'}))
            with mock.patch.object(mga.sys,'argv',['assistant','multiplier-mode','keep']):self.assertEqual(mga.cmd_multiplier_mode(),0)
            self.assertEqual(mga._multiplier_mode(),'keep');self.assertEqual(json.loads(p.read_text())['other'],'retained')
            p.write_text('{broken');self.assertEqual(mga._multiplier_mode(),'keep')


class DeviceHotplugTests(unittest.TestCase):
    def setUp(self):
        self.saved=(mga._active_serial,mga._device_session_ready,mga._continuous_mode)
        mga._active_serial=None;mga._device_session_ready=False

    def tearDown(self):
        mga._active_serial,mga._device_session_ready,mga._continuous_mode=self.saved

    def test_missing_unauthorized_offline_and_multiple_devices_stay_idle(self):
        for text,phase in [('List of devices attached\n','waiting_for_device'),
            ('List of devices attached\nphone-a unauthorized\n','waiting_for_debug_authorization'),
            ('phone-a offline\n','waiting_for_device_online'),
            ('phone-a device\nphone-b device\n','waiting_for_single_device')]:
            self.assertEqual(mga._select_adb_device(text),(None,phase))
        self.assertEqual(mga._select_adb_device('phone-a device\nphone-b device\n','phone-b'),('phone-b','device_ready'))

    def test_new_authorized_device_resets_old_game_state_and_binds_commands(self):
        mga._continuous_mode=True
        responses=[mock.Mock(returncode=0,stdout='phone-a device\n'),mock.Mock(returncode=0,stdout='phone-b device\n')]
        with mock.patch.object(mga.subprocess,'run',side_effect=responses),mock.patch.object(mga,'_reset_device_game_state') as reset,mock.patch.dict(os.environ,{},clear=True):
            self.assertTrue(mga.is_device_connected());self.assertEqual(mga._adb_args('shell','input','tap','10','20'),[mga.ADB,'-s','phone-a','shell','input','tap','10','20'])
            self.assertTrue(mga.is_device_connected());self.assertEqual(mga._active_serial,'phone-b');self.assertEqual(reset.call_count,2)

    def test_unauthorized_device_never_gets_input(self):
        mga._continuous_mode=True
        with mock.patch.object(mga.subprocess,'run',return_value=mock.Mock(returncode=0,stdout='phone-a unauthorized\n')) as run:
            self.assertFalse(mga.is_device_connected());self.assertFalse(mga.tap(10,20));self.assertFalse(mga.game_back());self.assertEqual(run.call_count,1)

    def test_waits_through_authorization_game_focus_and_layout_before_publishing(self):
        import tempfile,struct
        from pathlib import Path
        mga._continuous_mode=True
        stages=['none','unauthorized','other-app','wrong-layout','ready'];index=-1
        phases=[]
        def run(command,**kwargs):
            nonlocal index
            if command==[mga.ADB,'devices','-l']:
                index+=1
                state=stages[index]
                return mock.Mock(returncode=0,stdout='' if state=='none' else 'phone-a '+('unauthorized' if state=='unauthorized' else 'device')+'\n')
            self.assertEqual(command[:3],[mga.ADB,'-s','phone-a'])
            if 'dumpsys' in command:
                package='com.other.app' if stages[index]=='other-app' else 'com.scopely.monopolygo'
                return mock.Mock(returncode=0,stdout='mCurrentFocus=Window{123 u0 '+package+'/Game}')
            self.assertIn('screencap',command)
            data=struct.pack('<III',720,1280,1) if stages[index]=='wrong-layout' else struct.pack('<III',1080,2340,1)+bytes([0,0,0,255])*1080*2340
            return mock.Mock(returncode=0,stdout=data)
        with tempfile.TemporaryDirectory() as tmp,mock.patch.object(mga,'SCREENSHOT',str(Path(tmp)/'screen.png')),mock.patch.object(mga.subprocess,'run',side_effect=run),mock.patch.object(mga.time,'sleep') as sleep,mock.patch.object(mga,'report_phase',side_effect=phases.append),mock.patch.dict(os.environ,{},clear=True):
            mga.screenshot();self.assertEqual(mga.screen_image().size,(1080,2340));self.assertEqual(sleep.call_count,4)
        for phase in ['waiting_for_debug_authorization','waiting_for_game_focus','waiting_for_supported_layout']:
            self.assertIn(phase,phases)


class CaptureRetryTests(unittest.TestCase):
    def test_truncated_frame_keeps_old_file_until_success(self):
        import struct
        from pathlib import Path
        import tempfile
        raw=struct.pack('<IIII',1080,2340,1,0)+bytes([4,5,6,255])*(1080*2340)
        focus=mock.Mock(returncode=0,stdout='mCurrentFocus=Window{123 u0 com.scopely.monopolygo/Game}')
        with tempfile.TemporaryDirectory() as root:
            target=Path(root)/'screen.png'; target.write_bytes(b'old-frame')
            def wait(_): self.assertEqual(target.read_bytes(),b'old-frame')
            with mock.patch.object(mga,'SCREENSHOT',str(target)), mock.patch.object(mga,'_continuous_mode',True), mock.patch.object(mga,'is_device_connected',return_value=True), mock.patch.object(mga.subprocess,'run',side_effect=[focus,mock.Mock(returncode=0,stdout=raw[:100]),focus,mock.Mock(returncode=0,stdout=raw)]), mock.patch.object(mga.time,'sleep',side_effect=wait):
                mga.screenshot()
                self.assertEqual(mga.screen_image().getpixel((0,0)),(4,5,6))

    def test_wake_does_not_swipe_on_overlays(self):
        with mock.patch.object(mga,'sh') as shell:
            mga._keep_screen_awake()
            self.assertEqual(shell.call_count,1)
            self.assertIn('KEYCODE_WAKEUP',shell.call_args.args[0])

class NavigationRecoveryTests(unittest.TestCase):
    def test_unknown_popup_back_is_delayed_and_bounded(self):
        guard=mga.PopupRecovery()
        with mock.patch.object(mga,'game_back',return_value=True) as back, mock.patch.object(mga.time,'sleep'), mock.patch.object(mga.time,'monotonic',return_value=100):
            guard.handle()
            back.assert_not_called()
        with mock.patch.object(mga,'game_back',return_value=True) as back, mock.patch.object(mga.time,'sleep'), mock.patch.object(mga.time,'monotonic',return_value=120):
            for _ in range(6): guard.handle()
            self.assertEqual(back.call_count,2)
            guard.clear()
            guard.handle()
            self.assertEqual(back.call_count,2)

    def test_back_never_operates_on_external_billing(self):
        response=mock.Mock(returncode=0,stdout='mCurrentFocus=Window{123 u0 com.android.vending/Billing}')
        with mock.patch.object(mga.subprocess,'run',return_value=response) as run:
            self.assertFalse(mga.game_back())
            self.assertEqual(run.call_count,1)

    def test_build_back_fallback_verified(self):
        with mock.patch.object(mga,'_build_close_retry_after',0), mock.patch.object(mga,'screenshot'), mock.patch.object(mga,'is_build_menu_open',side_effect=[True]*5+[False]), mock.patch.object(mga.time,'sleep'), mock.patch.object(mga,'tap'), mock.patch.object(mga,'game_back',return_value=True) as back:
            self.assertEqual(mga.close_build_menu(),0)
            back.assert_called_once()

class OneDieEdgeTests(unittest.TestCase):
    def test_one_die_rounded_edge_counts_but_isolated_noise_does_not(self):
        from PIL import Image, ImageDraw
        image=Image.new('RGB',(1080,2340),(70,70,50))
        with mock.patch.object(mga,'screen_image',return_value=image):
            self.assertEqual(mga.get_roll_fill_ratio(),0)
            image.putpixel((377,2168),(30,180,230))
            self.assertEqual(mga.get_roll_fill_ratio(),0)
            ImageDraw.Draw(image).rectangle((376,2164,378,2173),fill=(30,180,230))
            self.assertGreaterEqual(mga.get_roll_fill_ratio(),mga.ROLL_RATIO_EMPTY)

class LastDieMultiplierTests(unittest.TestCase):
    def test_last_die_does_not_reprobe_maximum(self):
        with mock.patch.object(mga,'_last_die_detected',True), mock.patch.object(mga,'get_multiplier',return_value=(1,'x1')), mock.patch.object(mga,'_probe_multiplier_max') as probe, mock.patch.object(mga,'tap') as tap:
            self.assertEqual(mga._multiplier_action(),0)
            probe.assert_not_called();tap.assert_not_called()

    def test_last_die_returns_to_one_before_roll(self):
        with mock.patch.object(mga,'_last_die_detected',True), mock.patch.object(mga,'get_multiplier',side_effect=[(3,'x3'),(1,'x1')]), mock.patch.object(mga,'_multiplier_probe_blocked',return_value=False), mock.patch.object(mga,'screenshot'), mock.patch.object(mga.time,'sleep'), mock.patch.object(mga,'tap') as tap:
            self.assertEqual(mga._multiplier_action(),0)
            tap.assert_called_once_with(*mga.MULTIPLIER_BADGE)

class QuickWinsTests(unittest.TestCase):
    def setUp(self):
        patcher=mock.patch.object(mga,'is_wins_screen',return_value=False)
        patcher.start();self.addCleanup(patcher.stop)

    def test_badge_cooldown_prevents_reopening(self):
        with mock.patch.object(mga,'_last_wins_check',100), mock.patch.object(mga.time,'monotonic',return_value=110), mock.patch.object(mga,'cmd_check_wins') as wins:
            self.assertFalse(mga.maybe_check_wins());wins.assert_not_called()

    def test_badge_dispatches_when_due(self):
        with mock.patch.object(mga,'_last_wins_check',0), mock.patch.object(mga.time,'monotonic',return_value=400), mock.patch.object(mga,'is_wins_badge_present',return_value=True), mock.patch.object(mga,'_multiplier_probe_blocked',return_value=False), mock.patch.object(mga,'cmd_check_wins') as wins:
            self.assertTrue(mga.maybe_check_wins());wins.assert_called_once()

    def test_unrecognized_reward_label_never_tapped(self):
        with mock.patch.object(mga,'screenshot'), mock.patch.object(mga,'is_wins_screen',return_value=True), mock.patch.object(mga,'is_purchase_upsell_screen',return_value=False), mock.patch.object(mga,'find_green_button',return_value=(540,1200)), mock.patch.object(mga,'_confirmed_reward_button',return_value=None), mock.patch.object(mga,'game_back'), mock.patch.object(mga.time,'sleep'), mock.patch.object(mga,'tap') as tap:
            mga.cmd_check_wins()
            self.assertTrue(all(call.args == (540,2245) for call in tap.call_args_list))

class CollectDescriptionTest(unittest.TestCase):
    def test_task_description_is_not_a_button(self):
        rows=[]
        for number,word in enumerate(['Collect','1','Sticker'],1):
            rows.append(f'5\t1\t1\t1\t1\t{number}\t300\t1200\t100\t40\t95\t{word}')
        self.assertIsNone(mga._find_collect_word_from_tsv('\n'.join(rows)))

_chance_detector = mga.is_railroad_chance_card
_chance_default = mock.patch.object(mga,'is_railroad_chance_card',return_value=False)
_side_free_handler = mga.maybe_check_side_free_items
_boutique_handler = mga.handle_boutique
_boutique_default = mock.patch.object(mga,"handle_boutique",return_value=False)
_side_free_default = mock.patch.object(mga,'maybe_check_side_free_items',return_value=False)
_treasure_default = mock.patch.object(mga,'treasure_level',return_value=None)
def setUpModule():
    _side_free_default.start()
    _boutique_default.start()
    _treasure_default.start()
    _chance_default.start()
def tearDownModule():
    _side_free_default.stop()
    _boutique_default.stop()
    _treasure_default.stop()
    _chance_default.stop()

class TreasureTests(unittest.TestCase):
    def test_only_compact_star_clusters_are_tile_candidates(self):
        from PIL import Image,ImageDraw
        image=Image.new('RGB',(1080,2340),'black');d=ImageDraw.Draw(image)
        d.rectangle((510,1470,552,1512),fill=(76,151,234))
        d.rectangle((200,1200,400,1400),fill=(76,151,234))
        tiles=mga.treasure_tiles(image)
        self.assertEqual(len(tiles),1)
        self.assertTrue(510 <= tiles[0][0] <= 552)

    def test_gold_star_requires_blue_tile_background(self):
        from PIL import Image,ImageDraw
        image=Image.new('RGB',(1080,2340),'black'); d=ImageDraw.Draw(image)
        d.rectangle((490,1450,590,1550),fill=(107,166,242))
        d.rectangle((515,1475,565,1525),fill=(247,231,93))
        d.rectangle((300,1200,350,1250),fill=(247,231,93))
        tiles=mga.treasure_tiles(image)
        self.assertEqual(len(tiles),1)
        self.assertTrue(abs(tiles[0][0]-540)<5)

    def test_unreadable_hammers_prevents_spending(self):
        with mock.patch.object(mga,'treasure_level',return_value=2), mock.patch.object(mga,'ocr_region',side_effect=['','?']), mock.patch.object(mga.time,'sleep'), mock.patch.object(mga,'tap') as tap:
            self.assertTrue(mga.handle_treasure());tap.assert_not_called()

    def test_each_tile_has_retry_limit(self):
        with mock.patch.object(mga,'treasure_level',return_value=2), mock.patch.object(mga,'_dig_level',2), mock.patch.object(mga,'_dig_attempts',{}), mock.patch.object(mga,'ocr_region',side_effect=['','82']*4), mock.patch.object(mga,'screen_image',return_value=mock.Mock(getpixel=lambda p:(76,151,234))), mock.patch.object(mga,'treasure_tiles',return_value=[(540,1500)]), mock.patch.object(mga.time,'sleep'), mock.patch.object(mga,'tap') as tap:
            for _ in range(4): mga.handle_treasure()
            self.assertEqual(tap.call_count,2)

class TreasureExitTests(unittest.TestCase):
    def test_unchanged_state_exits_after_45_seconds(self):
        guard=mga.TreasureWatchdog()
        with mock.patch.object(mga.time,'monotonic',side_effect=[0,44,45]):
            self.assertFalse(guard.update((5,39)))
            self.assertFalse(guard.update((5,39)))
            self.assertTrue(guard.update((5,39)))

    def test_productive_play_is_not_ended_by_total_visit_time(self):
        guard=mga.TreasureWatchdog()
        with mock.patch.object(mga.time,'monotonic',side_effect=[0,40,80,600]):
            self.assertFalse(guard.update((1,84)))
            self.assertFalse(guard.update((1,83)))
            self.assertFalse(guard.update((2,82)))
            self.assertFalse(guard.update((9,1)))

    def test_exit_checks_screen_before_repeated_close(self):
        with mock.patch.object(mga,'_treasure_exit_retry',0), mock.patch.object(mga,'screenshot'), mock.patch.object(mga,'treasure_level',side_effect=[5,None]), mock.patch.object(mga.time,'sleep'), mock.patch.object(mga,'tap') as tap:
            mga.leave_treasure('test')
            tap.assert_called_once_with(540,2245)

class RailroadChanceTests(unittest.TestCase):
    def test_verified_text_required_even_on_matching_card(self):
        from PIL import Image
        image=Image.new('RGB',(1080,2340),'white')
        with mock.patch.object(mga,'screen_image',return_value=image), mock.patch.object(mga,'is_card_popup_screen',return_value=True), mock.patch.object(mga,'ocr_region',side_effect=['CHANCE','HEAD TO THE NEAREST RAILROAD IF YOU DARE']):
            self.assertTrue(_chance_detector())
        with mock.patch.object(mga,'screen_image',return_value=image), mock.patch.object(mga,'is_card_popup_screen',return_value=True), mock.patch.object(mga,'ocr_region',side_effect=['CHANCE','BUY DICE FOR $4.99']):
            self.assertFalse(_chance_detector())
        with mock.patch.object(mga,'screen_image',return_value=image), mock.patch.object(mga,'is_card_popup_screen',return_value=True), mock.patch.object(mga,'ocr_region',return_value='SPECIAL OFFER'):
            self.assertFalse(_chance_detector())

    def test_bounded_retry_and_reset_only_after_clear(self):
        with mock.patch.object(mga,'_chance_attempts',0), mock.patch.object(mga,'is_railroad_chance_card',return_value=True), mock.patch.object(mga.time,'sleep'), mock.patch.object(mga,'tap') as tap:
            for _ in range(4): self.assertTrue(mga.handle_railroad_chance())
            self.assertEqual(tap.call_count,2)
            tap.assert_called_with(540,1250)
            with mock.patch.object(mga,'is_railroad_chance_card',return_value=False), mock.patch.object(mga,'is_card_popup_screen',return_value=True):
                self.assertFalse(mga.handle_railroad_chance())
                self.assertEqual(mga._chance_attempts,2)
            with mock.patch.object(mga,'is_railroad_chance_card',return_value=False), mock.patch.object(mga,'is_card_popup_screen',return_value=False):
                self.assertFalse(mga.handle_railroad_chance())
                self.assertEqual(mga._chance_attempts,0)

class SideFreeItemsTests(unittest.TestCase):
    @staticmethod
    def tsv(text='FREE!', x=400, y=1200, confidence='95', line='1'):
        return '\t'.join(['5','1','1','1',line,'1',str(x),str(y),'110','40',confidence,text])

    def test_free_label_is_exact_confident_and_unambiguous(self):
        self.assertEqual(mga._exact_free_boxes(self.tsv()),[(400,1200,110,40)])
        for label in ('FREE $4.99','FREEBIE','NOT FREE','FREE AFTER PURCHASE','LOCKED FREE','FREE???'):
            self.assertEqual(mga._exact_free_boxes(self.tsv(label)),[])
        for confidence in ('30','nan','garbled'):
            self.assertEqual(mga._exact_free_boxes(self.tsv(confidence=confidence)),[])
        self.assertEqual(mga._exact_free_boxes(self.tsv()+'\n'+self.tsv('LOCKED')),[])

    def test_price_and_lock_contexts_are_rejected(self):
        self.assertTrue(mga._free_offer_context('DAILY GIFT FREE!'))
        for text in ('FREE GIFT $0.99','FREE GIFT 4.99','FREE GIFT UNLOCK','FREE GIFT LOCKED',
                     'FREE GIFT AFTER PURCHASE','FREE GIFT WATCH AD','FREE GIFT 100 USD','SPECIAL OFFER FREE'):
            self.assertFalse(mga._free_offer_context(text))

    def test_offer_requires_free_context_exact_button_and_shape(self):
        from PIL import Image
        tsv=self.tsv('DAILY GIFT',x=300,y=600,line='1')+'\n'+self.tsv(line='2')
        with mock.patch.object(mga,'is_purchase_upsell_screen',return_value=False), \
             mock.patch.object(mga,'screen_image',return_value=Image.new('RGB',(1080,2340))), \
             mock.patch.object(mga,'ocr_image',return_value=tsv), \
             mock.patch.object(mga,'find_green_button',return_value=(455,1190)), \
             mock.patch.object(mga,'ocr_region',return_value='FREE!'):
            self.assertEqual(mga._confirmed_free_offer_button(),(455,1190))
            with mock.patch.object(mga,'is_purchase_upsell_screen',return_value=True):
                self.assertIsNone(mga._confirmed_free_offer_button())
            with mock.patch.object(mga,'ocr_region',return_value='FREE AFTER PURCHASE'):
                self.assertIsNone(mga._confirmed_free_offer_button())
            with mock.patch.object(mga,'find_green_button',return_value=None):
                self.assertIsNone(mga._confirmed_free_offer_button())

    def test_checks_both_side_strips_only_on_verified_board(self):
        from PIL import Image
        with mock.patch.object(mga,'screen_image',return_value=Image.new('RGB',(1080,2340))), \
             mock.patch.object(mga,'is_card_popup_screen',return_value=False), \
             mock.patch.object(mga,'ocr_region',return_value='WINS ALBUM FRIENDS 0/60'), \
             mock.patch.object(mga,'ocr_image',return_value=self.tsv(x=50,y=200)) as ocr:
            self.assertEqual(mga._side_free_icon_candidates(),[(105,640),(955,640)])
            self.assertEqual(ocr.call_count,2)
            with mock.patch.object(mga,'is_card_popup_screen',return_value=True):
                self.assertEqual(mga._side_free_icon_candidates(),[])
            with mock.patch.object(mga,'ocr_region',return_value='BUILD'):
                self.assertEqual(mga._side_free_icon_candidates(),[])

    def test_free_chain_stops_before_paid_step_and_obeys_cooldown(self):
        with mock.patch.object(mga,'_last_side_free_check',float('-inf')), \
             mock.patch.object(mga,'_side_free_visits',{}), mock.patch.object(mga.time,'monotonic',return_value=1000), \
             mock.patch.object(mga.time,'sleep'), mock.patch.object(mga,'screenshot'), \
             mock.patch.object(mga,'_side_free_icon_candidates',return_value=[(100,600)]), \
             mock.patch.object(mga,'_confirmed_free_offer_button',side_effect=[(500,1200),None]), \
             mock.patch.object(mga,'is_collect_screen',return_value=False), \
             mock.patch.object(mga,'ocr_region',return_value='WINS ALBUM FRIENDS 0/60'), \
             mock.patch.object(mga,'tap',return_value=True) as tap:
            self.assertTrue(_side_free_handler())
            self.assertFalse(_side_free_handler())
            self.assertEqual(tap.call_args_list,[mock.call(100,600),mock.call(500,1200)])

    def test_unconfirmed_offer_only_returns_without_body_tap(self):
        with mock.patch.object(mga,'_last_side_free_check',float('-inf')), \
             mock.patch.object(mga,'_side_free_visits',{}), mock.patch.object(mga.time,'sleep'), \
             mock.patch.object(mga,'screenshot'), mock.patch.object(mga,'_side_free_icon_candidates',return_value=[(100,600)]), \
             mock.patch.object(mga,'_confirmed_free_offer_button',return_value=None), \
             mock.patch.object(mga,'is_collect_screen',return_value=False), \
             mock.patch.object(mga,'ocr_region',return_value='LOCKED OFFER'), \
             mock.patch.object(mga,'game_back',return_value=True) as back, \
             mock.patch.object(mga,'tap',return_value=True) as tap:
            self.assertTrue(_side_free_handler())
            tap.assert_called_once_with(100,600);back.assert_called_once()


class BoutiqueTest(unittest.TestCase):
    def setUp(self):
        self.transition=mock.patch.object(mga,"_handle_boutique_transition",return_value=False)
        self.transition.start();self.addCleanup(self.transition.stop)
        env=mock.patch.dict(os.environ,MONOPOLY_BOUTIQUE_AUTOPLAY="1")
        env.start();self.addCleanup(env.stop)

    def test_deferred_minigame_never_places_blocks(self):
        with mock.patch.dict(os.environ,MONOPOLY_BOUTIQUE_AUTOPLAY="0"),mock.patch.object(mga,'_is_boutique_board',return_value=True),mock.patch.object(mga,'_boutique_state') as state,mock.patch.object(mga,'_boutique_drag') as drag,mock.patch.object(mga.time,'sleep'):
            self.assertTrue(_boutique_handler());state.assert_not_called();drag.assert_not_called()

    def test_transition_context_requires_event_and_rejects_price(self):
        self.assertEqual(mga._boutique_transition_label("GRAND PRIZE! Fill 1 row and 1 column to win"),"NEXT")
        self.assertEqual(mga._boutique_transition_label("BLOCKS BOUTIQUE RECIPE COMPLETE!"),"COLLECT")
        self.assertIsNone(mga._boutique_transition_label("Grand prize NEXT"))
        self.assertIsNone(mga._boutique_transition_label("GRAND PRIZE Fill 1 row and 1 column $1.99"))

    def fixture(self,name="boutique-board.png"):
        from PIL import Image
        with Image.open(os.path.join(os.path.dirname(__file__),'fixtures',name)) as im:
            return im.convert('RGB')

    def test_live_frame_grid_and_pieces(self):
        with mock.patch.object(mga,'screen_image',return_value=self.fixture()), mock.patch.object(mga,'ocr_region',side_effect=['Recipe Merch item 1','12']):
            board,materials,count,pieces=mga._boutique_state()
        self.assertEqual(count,12);self.assertEqual(materials,frozenset((1,c) for c in range(4,8)))
        self.assertEqual([(p[1],p[2]) for p in pieces],[(2,3)]*3)
        move=mga._boutique_move(board,materials,pieces)
        self.assertEqual(move[2:6],(2,4,2,3))
        self.assertTrue(all(not move[-1][r][4] and not move[-1][r][5] for r in range(8)))

    def test_dimmed_overlay_cannot_spend(self):
        from PIL import ImageEnhance
        im=ImageEnhance.Brightness(self.fixture()).enhance(0.3)
        with mock.patch.object(mga,'screen_image',return_value=im),mock.patch.object(mga,'ocr_region',return_value='Recipe Merch item 1'):
            self.assertIsNone(mga._boutique_state())

    def test_unreadable_tokens_and_disconnected_piece_rejected(self):
        im=self.fixture()
        with mock.patch.object(mga,'screen_image',return_value=im),mock.patch.object(mga,'ocr_region',side_effect=['Recipe Merch item 1','?']):
            self.assertIsNone(mga._boutique_state())
        # A disconnected drawer fragment is not a valid piece.
        from PIL import ImageDraw
        ImageDraw.Draw(im).rectangle((245,1880,332,1930),fill=(100,60,155))
        with mock.patch.object(mga,'screen_image',return_value=im),mock.patch.object(mga,'ocr_region',side_effect=['Recipe Merch item 1','12']):
            self.assertIsNone(mga._boutique_state())

    def test_observed_l_t_shapes_and_carried_materials(self):
        with mock.patch.object(mga,'screen_image',return_value=self.fixture('boutique-shapes.png')),mock.patch.object(mga,'ocr_region',side_effect=['Recipe Merch item 2','10']):
            board,materials,count,pieces=mga._boutique_state()
        self.assertEqual(len(materials),8)
        self.assertEqual(pieces[0][4],((0,0),(1,0),(2,0),(2,1)))
        self.assertEqual(pieces[0][5],((1,0),))
        self.assertEqual(pieces[1][4],((0,0),(0,1),(0,2),(1,1)))
        move=mga._boutique_move(board,materials,pieces)
        self.assertEqual(move[1:6],(2,3,2,2,2))

    def test_sparse_shape_can_fit_around_existing_cell(self):
        board=[[0]*8 for _ in range(8)];board[1][1]=1
        shape=((0,0),(0,1),(1,0))
        self.assertIn((0,0),mga._boutique_placements(board,2,2,shape))
        self.assertNotIn((0,0),mga._boutique_placements(board,2,2))

    def test_no_legal_move_on_full_board(self):
        board=tuple((1,)*8 for _ in range(8))
        self.assertIsNone(mga._boutique_move(board,frozenset(),((0,2,3,(280,1900)),)))

    def test_zero_tokens_only_exits(self):
        state=(tuple((0,)*8 for _ in range(8)),frozenset(),0,())
        with mock.patch.object(mga,'_boutique_state',return_value=state),mock.patch.object(mga.time,'sleep'),mock.patch.object(mga,'game_back') as back,mock.patch.object(mga,'_boutique_drag') as drag:
            self.assertTrue(_boutique_handler());back.assert_called_once();drag.assert_not_called()

    def test_unknown_board_pauses_instead_of_generic_fallback(self):
        with mock.patch.object(mga,'_boutique_state',return_value=None),mock.patch.object(mga,'_is_boutique_board',return_value=True),mock.patch.object(mga.time,'sleep'),mock.patch.object(mga,'_boutique_drag') as drag:
            self.assertTrue(_boutique_handler());drag.assert_not_called()

    def test_drag_blocks_wrong_foreground(self):
        result=mock.Mock(returncode=0,stdout='mCurrentFocus=Window{ u0 com.android.vending/Billing}')
        with mock.patch.object(mga.subprocess,'run',return_value=result) as run:
            self.assertFalse(mga._boutique_drag((500,1900),(600,1500)))
            self.assertEqual(run.call_count,1)

    def test_drag_releases_if_focus_changes_after_down(self):
        game=mock.Mock(returncode=0,stdout='mCurrentFocus=Window{ u0 com.scopely.monopolygo/Main}')
        other=mock.Mock(returncode=0,stdout='mCurrentFocus=Window{ u0 com.android.vending/Billing}')
        with mock.patch.object(mga.subprocess,'run',side_effect=[game,mock.Mock(returncode=0),other,mock.Mock(returncode=0)]) as run:
            self.assertFalse(mga._boutique_drag((500,1900),(600,1500)))
            self.assertEqual(run.call_args_list[-1].args[0][-3:],['UP','600','1500'])


if __name__ == '__main__':
    unittest.main()
