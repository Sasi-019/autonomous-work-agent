from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)


PLAYWRIGHT = None
BROWSER = None
PAGE = None

PROFILE_PATH = "browser_profile"


# ============================================================
# BROWSER LIFECYCLE
# ============================================================

def start_browser():
    global PLAYWRIGHT
    global BROWSER
    global PAGE

    if PAGE is not None:
        try:
            if not PAGE.is_closed():
                return PAGE
        except Exception:
            pass

    PLAYWRIGHT = sync_playwright().start()

    BROWSER = PLAYWRIGHT.chromium.launch_persistent_context(
        PROFILE_PATH,
        channel="chrome",
        headless=False,
        viewport={
            "width": 1440,
            "height": 900,
        },
    )

    if BROWSER.pages:
        PAGE = BROWSER.pages[0]
    else:
        PAGE = BROWSER.new_page()

    return PAGE


def close_browser():
    global PLAYWRIGHT
    global BROWSER
    global PAGE

    try:
        if BROWSER:
            BROWSER.close()
    finally:
        BROWSER = None
        PAGE = None

        if PLAYWRIGHT:
            PLAYWRIGHT.stop()

        PLAYWRIGHT = None


def get_current_page():
    return start_browser()


# ============================================================
# WAITING
# ============================================================

def wait_after_action(page):
    try:
        page.wait_for_load_state(
            "domcontentloaded",
            timeout=5000,
        )
    except PlaywrightTimeoutError:
        pass

    page.wait_for_timeout(1000)


# ============================================================
# OPEN WEBSITE
# ============================================================

def open_website(url):
    if not url:
        return {
            "success": False,
            "message": "No URL provided.",
        }

    page = start_browser()

    try:
        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        wait_after_action(page)

        return {
            "success": True,
            "url": page.url,
            "title": page.title(),
        }

    except Exception as exc:
        return {
            "success": False,
            "message": str(exc),
            "url": page.url,
        }


# ============================================================
# LOCATOR HELPERS
# ============================================================

def _try_locator(
    page,
    locator,
):
    try:
        count = locator.count()

        if count > 0:
            return locator.first

    except Exception:
        pass

    return None


def _editable(locator):
    if locator is None:
        return False

    try:
        return locator.is_editable(
            timeout=2000
        )
    except Exception:
        return False


def resolve_locator(
    page,
    target=None,
    selector=None,
):
    """
    Resolve an element safely.

    IMPORTANT:
    Search/input selectors are checked BEFORE generic role
    matching.

    This prevents Google's voice-search button from being
    mistaken for the actual search textbox.
    """

    # --------------------------------------------------------
    # Explicit selector
    # --------------------------------------------------------

    if selector:
        locator = _try_locator(
            page,
            page.locator(selector),
        )

        if locator:
            return locator

    if not target:
        return None

    target = target.strip()
    lowered = target.lower()

    # --------------------------------------------------------
    # SEARCH-SPECIFIC RESOLUTION
    # --------------------------------------------------------

    if (
        "search" in lowered
        or "query" in lowered
    ):

        search_candidates = [
            "textarea[name='q']",
            "input[name='q']",
            "input[type='search']",
            "textarea[aria-label*='Search' i]",
            "input[aria-label*='Search' i]",
            "textarea[title*='Search' i]",
            "input[title*='Search' i]",
            "input[placeholder*='Search' i]",
        ]

        for candidate in search_candidates:
            try:
                locator = page.locator(candidate)

                count = locator.count()

                for index in range(count):
                    candidate_locator = (
                        locator.nth(index)
                    )

                    if _editable(
                        candidate_locator
                    ):
                        return candidate_locator

            except Exception:
                continue

    # --------------------------------------------------------
    # INPUT / TEXTBOX
    # --------------------------------------------------------

    for role in [
        "textbox",
        "combobox",
        "searchbox",
    ]:

        try:
            locator = page.get_by_role(
                role,
                name=target,
                exact=False,
            )

            count = locator.count()

            for index in range(count):
                candidate = locator.nth(index)

                if _editable(candidate):
                    return candidate

        except Exception:
            pass

    # --------------------------------------------------------
    # BUTTON / LINK
    # --------------------------------------------------------

    for role in [
        "button",
        "link",
    ]:

        try:
            locator = page.get_by_role(
                role,
                name=target,
                exact=False,
            )

            if locator.count() > 0:
                return locator.first

        except Exception:
            pass

    # --------------------------------------------------------
    # LABEL
    # --------------------------------------------------------

    try:
        locator = page.get_by_label(
            target,
            exact=False,
        )

        if locator.count() > 0:
            candidate = locator.first

            if (
                _editable(candidate)
                or not (
                    "search" in lowered
                    or "query" in lowered
                )
            ):
                return candidate

    except Exception:
        pass

    # --------------------------------------------------------
    # PLACEHOLDER
    # --------------------------------------------------------

    try:
        locator = page.get_by_placeholder(
            target,
            exact=False,
        )

        if locator.count() > 0:
            return locator.first

    except Exception:
        pass

    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    try:
        locator = page.get_by_text(
            target,
            exact=False,
        )

        if locator.count() > 0:
            return locator.first

    except Exception:
        pass

    return None


# ============================================================
# TYPE TEXT
# ============================================================

def type_text(
    text,
    url=None,
    selector=None,
    target=None,
    submit=False,
):
    page = start_browser()

    if url and (
        not page.url
        or page.url.rstrip("/")
        != url.rstrip("/")
    ):
        try:
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            wait_after_action(page)

        except Exception as exc:
            return {
                "success": False,
                "message": (
                    f"Navigation failed: {exc}"
                ),
            }

    locator = resolve_locator(
        page,
        target=target,
        selector=selector,
    )

    if locator is None:
        return {
            "success": False,
            "message": (
                "Could not find the requested "
                "editable input element."
            ),
            "url": page.url,
        }

    try:
        if not _editable(locator):
            return {
                "success": False,
                "message": (
                    "The resolved element is not "
                    "editable. A button or non-input "
                    "element was selected."
                ),
                "url": page.url,
            }

        locator.fill(text)

        if submit:
            locator.press("Enter")
            wait_after_action(page)

        return {
            "success": True,
            "url": page.url,
            "title": page.title(),
            "submitted": submit,
        }

    except Exception as exc:
        return {
            "success": False,
            "message": str(exc),
            "url": page.url,
        }


# ============================================================
# CLICK
# ============================================================

def click_element(
    url=None,
    selector=None,
    target=None,
):
    page = start_browser()

    if url and (
        not page.url
        or page.url.rstrip("/")
        != url.rstrip("/")
    ):
        try:
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            wait_after_action(page)

        except Exception as exc:
            return {
                "success": False,
                "message": (
                    f"Navigation failed: {exc}"
                ),
            }

    locator = resolve_locator(
        page,
        target=target,
        selector=selector,
    )

    if locator is None:
        return {
            "success": False,
            "message": (
                "Could not find the requested "
                "button/link/element."
            ),
            "url": page.url,
        }

    try:
        locator.click(
            timeout=10000
        )

        wait_after_action(page)

        return {
            "success": True,
            "url": page.url,
            "title": page.title(),
        }

    except Exception as exc:
        return {
            "success": False,
            "message": str(exc),
            "url": page.url,
        }


# ============================================================
# GOOGLE SEARCH
# ============================================================

def search_web(query):
    """
    Perform a complete Google search.

    This is deliberately implemented as one browser tool:

        open Google
             ↓
        locate actual search textbox
             ↓
        fill query
             ↓
        press Enter
             ↓
        wait
             ↓
        verify Google results page
    """

    if not query or not query.strip():
        return {
            "success": False,
            "message": "Search query is empty.",
        }

    query = query.strip()

    page = start_browser()

    try:

        # ----------------------------------------------------
        # OPEN GOOGLE
        # ----------------------------------------------------

        page.goto(
            "https://www.google.com/",
            wait_until="domcontentloaded",
            timeout=30000,
        )

        wait_after_action(page)

        # ----------------------------------------------------
        # FIND REAL SEARCH BOX
        # ----------------------------------------------------

        search_box = None

        google_selectors = [
            "textarea[name='q']",
            "input[name='q']",
            "input[type='search']",
        ]

        for selector in google_selectors:

            try:
                locator = page.locator(
                    selector
                )

                count = locator.count()

                for index in range(count):

                    candidate = locator.nth(
                        index
                    )

                    if _editable(candidate):
                        search_box = candidate
                        break

                if search_box:
                    break

            except Exception:
                continue

        # ----------------------------------------------------
        # FALLBACK
        # ----------------------------------------------------

        if search_box is None:

            try:
                locator = page.get_by_role(
                    "textbox"
                )

                count = locator.count()

                for index in range(count):

                    candidate = locator.nth(
                        index
                    )

                    if _editable(candidate):
                        search_box = candidate
                        break

            except Exception:
                pass

        if search_box is None:
            return {
                "success": False,
                "message": (
                    "Google search textbox was not found."
                ),
                "url": page.url,
            }

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        search_box.fill(query)

        search_box.press("Enter")

        # ----------------------------------------------------
        # WAIT FOR RESULTS
        # ----------------------------------------------------

        try:
            page.wait_for_load_state(
                "domcontentloaded",
                timeout=10000,
            )
        except PlaywrightTimeoutError:
            pass

        page.wait_for_timeout(1500)

        # ----------------------------------------------------
        # VERIFY
        # ----------------------------------------------------

        current_url = page.url.lower()

        if (
            "google.com/search"
            not in current_url
            and "q=" not in current_url
        ):
            return {
                "success": False,
                "message": (
                    "The search was submitted, "
                    "but Google results could not "
                    "be verified."
                ),
                "query": query,
                "url": page.url,
                "title": page.title(),
            }

        return {
            "success": True,
            "query": query,
            "url": page.url,
            "title": page.title(),
        }

    except Exception as exc:

        return {
            "success": False,
            "message": str(exc),
            "url": page.url,
        }