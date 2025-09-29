// Robust Mermaid initialization for MkDocs Material + GitHub Pages
(function () {
  function initMermaid() {
    if (!window.mermaid) return;

    // Convert fenced code blocks ```mermaid into <div class="mermaid"> if needed
    const codeBlocks = document.querySelectorAll('pre code.language-mermaid');
    codeBlocks.forEach((code) => {
      const pre = code.closest('pre');
      if (!pre) return;
      const container = document.createElement('div');
      container.className = 'mermaid';
      container.textContent = code.textContent;
      pre.replaceWith(container);
    });

    try {
      window.mermaid.initialize({ startOnLoad: true, securityLevel: 'loose' });
      window.mermaid.init(undefined, document.querySelectorAll('.mermaid'));
    } catch (e) {
      console.error('Mermaid init error:', e);
    }
  }

  // Run on initial load
  document.addEventListener('DOMContentLoaded', initMermaid);

  // Re-run on MkDocs Material page changes (instant loading)
  document.addEventListener('DOMContentLoaded', () => {
    const el = document.querySelector('body');
    if (!el) return;
    // Hook into DOM changes
    const observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        if (m.addedNodes && m.addedNodes.length) {
          initMermaid();
          break;
        }
      }
    });
    observer.observe(el, { childList: true, subtree: true });
  });
})();