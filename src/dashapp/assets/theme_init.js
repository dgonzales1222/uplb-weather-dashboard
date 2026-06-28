// Restore the saved dark-mode preference as early as possible.
(function () {
  try {
    if (localStorage.getItem("uplb-dark") === "1") {
      document.documentElement.classList.add("dark");
    }
  } catch (e) {}
})();
