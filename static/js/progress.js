/*running the script after the page has fully loaded */
document.addEventListener("DOMContentLoaded", () => {
    /*Selects the progress bar element and stops execution if it does not exist*/
    const bar = document.getElementById("progressBar");
    /*retrieving the target percentage value and initializes the current width */
    if (!bar) return;
    const target = parseInt(bar.getAttribute("aria-valuenow"));
    let width = 0;
    /*increasing the progress bar width using a timed interval,
      updates both the visual width and stops when target value is reached */
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
