(function () {
  function storageGet(store, key) {
    try {
      return store.getItem(key);
    } catch (e) {
      return null;
    }
  }

  function storageSet(store, key, value) {
    try {
      store.setItem(key, value);
    } catch (e) {}
  }

  function currentFile() {
    const pathname = window.location.pathname || "";
    if (pathname.endsWith("/")) return "index.html";
    const last = decodeURIComponent(pathname.split("/").pop() || "");
    if (!last) return "index.html";
    if (!/\.[A-Za-z0-9]+$/.test(last)) return last + ".html";
    return last;
  }

  function hrefParts(link) {
    const raw = link.getAttribute("href") || "";
    const hashIndex = raw.indexOf("#");
    const path = hashIndex === -1 ? raw : raw.slice(0, hashIndex);
    const hash = hashIndex === -1 ? "" : raw.slice(hashIndex + 1);
    const file = path ? currentFileFromHref(path) : currentFile();
    return { file: file, hash: decodeURIComponent(hash) };
  }

  function currentFileFromHref(path) {
    const last = decodeURIComponent((path || "").split("/").pop() || "");
    if (!last || last === "." ) return "index.html";
    if (!/\.[A-Za-z0-9]+$/.test(last)) return last + ".html";
    return last;
  }

  const desktopQuery = window.matchMedia("(min-width: 960px)");
  const topBar = document.querySelector(".book-top-bar");
  let lastScrollY = Math.max(0, window.scrollY);
  let topBarOffset = 0;

  function updateTopBar() {
    if (!topBar) return;
    const scrollY = Math.max(0, window.scrollY);
    if (desktopQuery.matches || scrollY <= 48 || document.body.classList.contains("drawer-open")) {
      topBarOffset = 0;
    } else {
      const delta = scrollY - lastScrollY;
      const barMovement = delta < 0 ? delta * 1.25 : delta;
      topBarOffset = Math.max(0, Math.min(topBar.offsetHeight, topBarOffset + barMovement));
    }
    lastScrollY = scrollY;
    topBar.style.transform = desktopQuery.matches ? "" : `translateY(-${topBarOffset}px)`;
    topBar.classList.toggle("is-hidden", !desktopQuery.matches && topBarOffset >= topBar.offsetHeight);
  }
  const tocLinks = Array.from(document.querySelectorAll("#sidebar-toc a"));
  const scroller = document.getElementById("sidebar");
  const pageFile = currentFile();
  const pageLinks = tocLinks.filter((link) => hrefParts(link).file === pageFile);

  function scrollSidebarTo(link) {
    if (!scroller || !link) return;
    const sRect = scroller.getBoundingClientRect();
    const lRect = link.getBoundingClientRect();
    const pad = 16;
    const visible = lRect.top >= sRect.top + pad && lRect.bottom <= sRect.bottom - pad;
    if (visible) return;
    scroller.scrollTop += lRect.top - sRect.top - scroller.clientHeight / 3;
  }

  function setActive(link) {
    tocLinks.forEach((item) => {
      const on = item === link;
      item.classList.toggle("active-chapter", on);
      if (on) item.setAttribute("aria-current", "location");
      else item.removeAttribute("aria-current");
    });
    if (link) scrollSidebarTo(link);
  }

  function linkForHash(hash) {
    if (!hash) return null;
    return pageLinks.find((link) => hrefParts(link).hash === hash) || null;
  }

  function headingTop(link) {
    const hash = hrefParts(link).hash;
    if (!hash) return Infinity;
    const heading = document.getElementById(hash);
    if (!heading) return Infinity;
    return heading.getBoundingClientRect().top;
  }

  function activeFromScroll() {
    if (!pageLinks.length) return null;
    const withHeading = pageLinks.filter((link) => headingTop(link) !== Infinity);
    const links = withHeading.length ? withHeading : pageLinks;
    const marker = 96;
    let current = links[0];
    links.forEach((link) => {
      if (headingTop(link) <= marker) current = link;
    });
    const hash = decodeURIComponent((window.location.hash || "").replace(/^#/, ""));
    if (hash) {
      const hashed = linkForHash(hash);
      const heading = document.getElementById(hash);
      if (hashed && heading && heading.getBoundingClientRect().top >= 0 && heading.getBoundingClientRect().top < window.innerHeight / 2) {
        return hashed;
      }
    }
    return current;
  }

  function updateActive() {
    setActive(activeFromScroll());
  }

  document.addEventListener("keydown", function (e) {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.isContentEditable) return;
    if (e.key === "ArrowLeft") {
      const prev = document.querySelector("a[rel='previous']");
      if (prev && prev.href) window.location.href = prev.href;
    } else if (e.key === "ArrowRight") {
      const next = document.querySelector("a[rel='next']");
      if (next && next.href) window.location.href = next.href;
    } else if (e.key === "Escape") {
      closeDrawer();
    }
  });

  if (scroller) {
    scroller.addEventListener("scroll", () => {
      storageSet(sessionStorage, "vellum-sidebar-scroll", String(scroller.scrollTop));
    });
  }

  let resizeTimeout;
  window.addEventListener("resize", () => {
    updateTopBar();
    document.documentElement.classList.add("no-transitions");
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
      document.documentElement.classList.remove("no-transitions");
    }, 100);
  });

  const toggleBtn = document.getElementById("sidebar-toggle");
  const sidebarEl = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");

  function setDrawerOpen(open) {
    if (!sidebarEl || !backdrop) return;
    sidebarEl.classList.add("drawer-animating");
    sidebarEl.classList.toggle("open", open);
    backdrop.classList.toggle("open", open);
    document.body.classList.toggle("drawer-open", open);
    updateTopBar();
  }

  function closeDrawer() {
    setDrawerOpen(false);
  }

  function toggleSidebar() {
    if (desktopQuery.matches) {
      const isCollapsed = document.documentElement.classList.toggle("sidebar-collapsed");
      storageSet(localStorage, "vellum-sidebar-collapsed", isCollapsed ? "true" : "false");
    } else {
      setDrawerOpen(!sidebarEl.classList.contains("open"));
    }
  }

  if (toggleBtn) toggleBtn.addEventListener("click", toggleSidebar);
  if (backdrop) backdrop.addEventListener("click", closeDrawer);

  window.addEventListener("hashchange", updateActive);
  window.addEventListener(
    "scroll",
    () => {
      if (window.__vellumSpyFrame) return;
      window.__vellumSpyFrame = requestAnimationFrame(() => {
        window.__vellumSpyFrame = null;
        updateActive();
        updateTopBar();
      });
    },
    { passive: true }
  );

  tocLinks.forEach((link) => {
    link.addEventListener("click", () => {
      const parts = hrefParts(link);
      if (parts.file === pageFile) {
        setActive(link);
        if (!desktopQuery.matches) closeDrawer();
      }
    });
  });

  updateActive();
  updateTopBar();
})();
