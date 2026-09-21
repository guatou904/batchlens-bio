"""Exercise the installed workbench in a real browser; keep all synthetic evidence."""

import argparse
import hashlib
import io
import json
import sys
import threading
import zipfile
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright

from batchlens import __version__
from batchlens.service import CASES
from batchlens.web import AuditServer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--channel", default="chrome" if sys.platform == "darwin" else "")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    checks, errors, external = [], [], []
    resources = files("batchlens").joinpath("resources")
    balanced = resources.joinpath("quick-demo/balanced.csv").read_bytes()
    with AuditServer(out / "audits") as server, sync_playwright() as playwright:
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        browser = playwright.chromium.launch(channel=args.channel or None)
        context = browser.new_context(
            viewport={"width": 1440, "height": 1050}, reduced_motion="reduce"
        )
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "request",
            lambda request: (
                external.append(request.url)
                if urlsplit(request.url).hostname not in {"localhost", "127.0.0.1", None}
                else None
            ),
        )

        def ready():
            expect(page.locator("#busy")).to_be_hidden()

        def snapshot(name):
            ready()
            page.screenshot(path=str(out / f"{name}.png"), full_page=True)
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
                f"Horizontal overflow: {name}"
            )

        def document():
            href = page.locator('a[download][href$="result.json"]').get_attribute("href")
            response = context.request.get(server.url + href)
            assert response.ok
            return response.json()

        def demo(case, status):
            page.select_option("#demo-case", case)
            with page.expect_response(lambda r: "/api/" in r.url and "/demo/" in r.url):
                page.click("#demo")
            ready()
            expect(page.locator("#results")).to_be_visible()
            result = document()
            assert result["contrasts"][0]["status"] == status
            assert page.locator("#results").evaluate("e => e === document.activeElement")
            mode = page.locator("[data-mode][aria-selected=true]").get_attribute("data-mode")
            checks.append(f"{mode} demo {case}: {status}")
            return result

        try:
            page.goto(server.url)
            expect(page.locator("#version")).to_contain_text(__version__)
            snapshot("home-zh")
            for case, status in [
                ("confounded", "NON_ESTIMABLE"),
                ("balanced", "ESTIMABLE"),
                ("paired", "ESTIMABLE"),
            ]:
                demo(case, status)
                if case == "confounded":
                    page.locator(".finding[open] .evidence > summary").first.click()
                    expect(page.locator(".finding[open] .evidence pre").first).to_be_visible()
                    assert len(page.locator(".finding[open] .evidence pre").first.inner_text()) > 10
            snapshot("paired-zh")
            page.click("#language")
            expect(page.locator("html")).to_have_attribute("lang", "en")
            snapshot("home-en")
            page.locator("#mode-quick").focus()
            page.keyboard.press("ArrowRight")
            expect(page.locator("#mode-advanced")).to_be_focused()
            expected = [
                "ESTIMABLE",
                "NON_ESTIMABLE",
                "ESTIMABLE",
                "ESTIMABLE",
                "ESTIMABLE",
                "NOT_ASSESSED",
                "NOT_ASSESSED",
            ]
            for case, status in zip(CASES, expected, strict=True):
                demo(case, status)
            checks.append("Keyboard navigation and all seven original scenarios")

            # Whole-group drop and individual slot drop preserve the original UI workflow.
            uploads = [
                {"name": name, "text": resources.joinpath(f"demo/balanced/{name}").read_text()}
                for name in ("samples.tsv", "design.yaml")
            ]
            page.evaluate(
                """items => {const data = new DataTransfer();
                for(const item of items)data.items.add(new File([item.text],item.name));
                document.querySelector('#advanced-drop').dispatchEvent(new DragEvent('drop',
                  {dataTransfer:data,bubbles:true,cancelable:true}));} """,
                uploads,
            )
            ready()
            expect(page.locator("#run")).to_be_enabled()
            page.evaluate(
                """item => {const data = new DataTransfer();
                data.items.add(new File([item.text], 'custom-sample-name.tsv'));
                document.querySelector('[data-drop-role="samples"]').dispatchEvent(
                new DragEvent('drop', {dataTransfer:data,bubbles:true,cancelable:true}));}""",
                uploads[0],
            )
            ready()
            expect(page.locator('[data-drop-role="samples"]')).to_contain_text(
                "custom-sample-name.tsv"
            )
            page.click("#run")
            ready()
            assert document()["contrasts"][0]["status"] == "ESTIMABLE"
            checks.append("Advanced group and individual-slot drag/drop and audit")

            page.click("#mode-quick")
            page.locator("#cell-file").set_input_files(
                {"name": "study.csv", "mimeType": "text/csv", "buffer": balanced}
            )
            ready()
            expect(page.locator("#numerator")).to_have_value("")
            expect(page.locator("#design-mode")).to_have_value("")
            expect(page.locator("#role-timepoint")).to_have_value("")
            expect(page.locator("#run")).to_be_disabled()
            page.select_option("#role-batch", "donor")
            ready()
            expect(page.locator("#run")).to_be_disabled()
            expect(page.locator("#role-batch")).to_be_focused()
            page.select_option("#role-batch", "batch")
            ready()
            page.select_option("#numerator", "regeneration")
            page.select_option("#denominator", "control")
            page.select_option("#design-mode", "independent")
            page.click("#thresholds > summary")
            page.fill("#setting-min_units", "1")
            expect(page.locator("#run")).to_be_disabled()
            page.fill("#setting-min_units", "3")
            expect(page.locator("#run")).to_be_enabled()
            snapshot("mapped-en")
            page.click("#run")
            ready()
            original = document()
            assert original["counts"]["experimental_units"] == 6
            assert original["counts"]["observations"] == 720
            assert original["contrasts"][0]["status"] == "ESTIMABLE"
            snapshot("balanced-en")
            checks.append(
                "Real CSV import, explicit comparison, mapping focus and threshold validation"
            )

            count = len(server.bundles)
            page.click("#language")
            assert document() == original and len(server.bundles) == count
            for selector, suffix in [("#download-html", ".html"), ("#download-zip", ".zip")]:
                with page.expect_download() as pending:
                    page.click(selector)
                data = Path(pending.value.path()).read_bytes()
                if suffix == ".html":
                    assert b'lang="zh"' in data
                else:
                    with zipfile.ZipFile(io.BytesIO(data)) as bundle:
                        prefix = (
                            next(
                                n for n in bundle.namelist() if n.endswith("/manifest.json")
                            ).rsplit("/", 1)[0]
                            + "/"
                        )
                        manifest = json.loads(bundle.read(prefix + "manifest.json"))
                        for name, digest in manifest["outputs"].items():
                            assert hashlib.sha256(bundle.read(prefix + name)).hexdigest() == digest
                        assert json.loads(bundle.read(prefix + "result.json")) == original
            checks.append("Language switch preserves results; actual HTML/ZIP downloads and hashes")
            page.click("#tab-report")
            expect(page.frame_locator("#report").locator("html")).to_have_attribute("lang", "zh")
            page.frame_locator("#report").locator("h1").wait_for()
            snapshot("report-zh")
            page.click("#tab-overview")
            page.click('[data-filter="warning"]')
            expect(page.locator('[data-filter="warning"]')).to_be_focused()
            page.click('[data-filter="all"]')
            page.click("#handoff")
            ready()
            assert len(server.bundles) == count
            expect(page.locator("#mode-advanced")).to_have_attribute("aria-selected", "true")
            expect(page.locator("#input-panel")).to_be_focused()
            expect(page.locator('[data-download-input="observations"]')).to_be_visible()
            snapshot("handoff-zh")
            page.click("#run")
            ready()
            advanced = document()
            assert {k: v for k, v in original.items() if k != "input_adapter"} == advanced
            checks.append("Quick-to-advanced handoff preserves every scientific JSON field")

            for language in ("zh", "en"):
                if page.locator("html").get_attribute("lang") != (
                    "zh-CN" if language == "zh" else "en"
                ):
                    page.click("#language")
                page.set_viewport_size({"width": 390, "height": 844})
                snapshot(f"mobile-advanced-{language}")
                page.click("#mode-quick")
                snapshot(f"mobile-quick-{language}")
                page.click("#tab-report")
                page.frame_locator("#report").locator("h1").wait_for()
                snapshot(f"mobile-report-{language}")
                assert page.locator("#report").evaluate(
                    "e => e.contentDocument.documentElement.scrollWidth <= e.clientWidth"
                )
                page.click("#mode-advanced")
            checks.append("390px mobile layouts and embedded reports in both languages")

            page.set_viewport_size({"width": 1440, "height": 1050})
            page.click("#mode-quick")
            for name, raw in [
                ("bad.csv", b"a,b\n\xff,1"),
                ("bad.csv", b"a,a\n1,2"),
                ("bad.exe", balanced),
            ]:
                page.locator("#cell-file").set_input_files(
                    {"name": name, "mimeType": "text/plain", "buffer": raw}
                )
                ready()
                expect(page.locator("#status")).to_be_visible()
                expect(page.locator("#status")).to_be_focused()
            hostile = 'study<img src=x onerror="window.__injected=1">.csv'
            page.locator("#cell-file").set_input_files(
                {"name": hostile, "mimeType": "text/csv", "buffer": balanced}
            )
            ready()
            expect(page.locator(".file-summary strong")).to_have_text(hostile)
            assert page.evaluate("window.__injected") is None
            checks.append("Malformed inputs show focused errors; filename markup stays inert")
            assert not errors, errors
            assert not external, external
            (out / "browser-qa.json").write_text(
                json.dumps(
                    {
                        "version": __version__,
                        "browser": browser.version,
                        "checks": checks,
                        "javascript_errors": errors,
                        "external_requests": external,
                        "synthetic_only": True,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            print(f"{len(checks)} browser checks passed; evidence: {out}")
        finally:
            browser.close()
            server.shutdown()
            worker.join(timeout=10)


if __name__ == "__main__":
    main()
