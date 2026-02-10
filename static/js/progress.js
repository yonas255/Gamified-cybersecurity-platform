document.addEventListener("DOMContentLoaded", () => {
    const bar = document.getElementById("progressBar");
    if (!bar) return;

    const target = parseInt(bar.getAttribute("aria-valuenow"));
    let width = 0;

    const interval = setInterval(() => {
        if (width >= target) {
            clearInterval(interval);
        } else {
            width++;
            bar.style.width = width + "%";
            bar.textContent = width + "%";
        }
    }, 15);
});
